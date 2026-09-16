import multiprocessing
import os
import sys
import threading
from pathlib import Path

import pytest
import uvicorn
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy

from definitions import PROJECT_ROOT_PATH

APPLICATION_HOST = "0.0.0.0"
APPLICATION_PORT = 8000
HTTP_STUB_PORT = 8080


class UvicornServer(multiprocessing.Process):
    def __init__(self, config: uvicorn.Config):
        super().__init__()
        self.server = uvicorn.Server(config=config)
        self.config = config

    def stop(self):
        self.terminate()

    def run(self, *args, **kwargs):
        self.server.run()


def stream_container_logs(container: DockerContainer, name=None):
    def _stream():
        for line in container.get_wrapped_container().logs(stream=True, follow=True):
            text = line.decode(errors="ignore").rstrip()
            prefix = f"[{name}] " if name else ""
            print(f"{prefix}{text}", flush=True)

    thread = threading.Thread(target=_stream, daemon=True)
    thread.start()
    return thread


@pytest.fixture(scope="module")
def api_service():
    config = uvicorn.Config("app.main:app", host=APPLICATION_HOST, port=APPLICATION_PORT, log_level="info")
    server = UvicornServer(config)
    server.start()
    try:
        yield server
    finally:
        server.stop()
        server.join(timeout=10)
        if server.is_alive():
            server.kill()
            server.join(timeout=10)



def specmatic_container():
    container = DockerContainer("specmatic/specmatic")
    for name, value in os.environ.items():
        container.with_env(name, value)

    container = (
        container
        .with_volume_mapping(str(Path.home() / ".specmatic"), "/specmatic", mode="ro")
        .with_env("SPECMATIC_LICENSE_PATH", "/specmatic/specmatic-license.txt")
        .with_env("JAVA_OPTS", "-Dspecmatic.logging.level=trace -Dspecmatic.logging.stdout.enabled=true")
        .with_volume_mapping(str(PROJECT_ROOT_PATH), "/usr/src/app", mode="rw")
        .with_env("GIT_DISCOVERY_ACROSS_FILESYSTEM", "1")
        .with_env("GIT_CONFIG_COUNT", "1")
        .with_env("GIT_CONFIG_KEY_0", "safe.directory")
        .with_env("GIT_CONFIG_VALUE_0", "/usr/src/app")
        .with_kwargs(
            extra_hosts={"host.docker.internal": "host-gateway"},
            working_dir="/usr/src/app",
        )
    )
    return container


@pytest.fixture(scope="module")
def mock_container():
    container = (
        specmatic_container()
        .with_command(["mock"])
        .with_bind_ports(HTTP_STUB_PORT, HTTP_STUB_PORT)
        .waiting_for(HttpWaitStrategy(HTTP_STUB_PORT, path="/actuator/health").with_method("GET").for_status_code(200))
    )
    thread = None
    try:
        container.start()
        thread = stream_container_logs(container, name="specmatic-stub")
        yield container
    finally:
        try:
            wrapped = container.get_wrapped_container()
            if wrapped is not None:
                wrapped.reload()
                if wrapped.status == "running":
                    # Let the mock finish writing and sending reports before removal.
                    wrapped.kill(signal="SIGINT")
                    wrapped.wait(timeout=300)
        finally:
            try:
                container.stop()
            finally:
                if thread is not None:
                    thread.join(timeout=10)


@pytest.fixture(scope="module")
def test_container(api_service, mock_container):
    container = (
        specmatic_container()
        .with_command(["test"])
        .with_env("APP_URL", f"http://host.docker.internal:{APPLICATION_PORT}")
    )
    thread = None
    try:
        container.start()
        thread = stream_container_logs(container, name="specmatic-test")
        yield container
    finally:
        try:
            container.stop()
        finally:
            if thread is not None:
                thread.join(timeout=10)


@pytest.mark.skipif(
    os.environ.get("CI") == "true" and not sys.platform.startswith("linux"),
    reason="Run only on Linux CI; all platforms allowed locally",
)
def test_contract(api_service, mock_container, test_container):
    try:
        result = test_container.get_wrapped_container().wait(timeout=300)
    except Exception as error:
        stdout, stderr = test_container.get_logs()
        logs = (stdout + stderr).decode("utf-8", errors="replace")
        raise AssertionError(f"Could not wait for contract test completion; container logs:\n{logs}") from error

    stdout, stderr = test_container.get_logs()
    stdout = stdout.decode("utf-8", errors="replace")
    stderr = stderr.decode("utf-8", errors="replace")
    logs = f"Contract test container logs:\n{stdout}\n{stderr}"
    assert result["StatusCode"] == 0, logs
    assert "Failures: 0" in stdout, logs
