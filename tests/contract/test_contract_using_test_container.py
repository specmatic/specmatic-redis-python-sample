import multiprocessing
import os
import sys
import threading

import pytest
import uvicorn
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy, LogMessageWaitStrategy

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
            print(f"{prefix}{text}")

    thread = threading.Thread(target=_stream, daemon=True)
    thread.start()
    return thread


@pytest.fixture(scope="module")
def api_service():
    config = uvicorn.Config("app.main:app", host=APPLICATION_HOST, port=APPLICATION_PORT, log_level="info")
    server = UvicornServer(config)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope="module")
def mock_container():
    examples_path = str(PROJECT_ROOT_PATH / "tests" / "contract"/ "data")
    specmatic_yaml_path = str(PROJECT_ROOT_PATH / "specmatic.yaml")
    build_reports_path = str(PROJECT_ROOT_PATH / "build/reports/specmatic")
    container = (
        DockerContainer("specmatic/specmatic")
        .with_command(["mock"])
        .with_bind_ports(HTTP_STUB_PORT, HTTP_STUB_PORT)
        .with_volume_mapping(examples_path, "/usr/src/app/test/data", mode="ro")
        .with_volume_mapping(specmatic_yaml_path, "/usr/src/app/specmatic.yaml", mode="ro")
        .with_volume_mapping(build_reports_path, "/usr/src/app/build/reports/specmatic", mode="rw")
        .waiting_for(HttpWaitStrategy(HTTP_STUB_PORT, path="/actuator/health").with_method("GET").for_status_code(200))
    )
    container.start()
    thread = stream_container_logs(container, name="specmatic-mock")
    yield container

    wrapped = container.get_wrapped_container()  # docker SDK container

    # Ask the process to shut down like Ctrl+C
    wrapped.kill(signal="SIGINT")

    # Then wait up to 30s for it to stop cleanly (and write reports)
    wrapped.wait(timeout=30)

    thread.join()


@pytest.fixture(scope="module")
def test_container():
    specmatic_yaml_path = str(PROJECT_ROOT_PATH / "specmatic.yaml")
    build_reports_path = str(PROJECT_ROOT_PATH / "build/reports/specmatic")
    container = (
        DockerContainer("specmatic/specmatic")
        .with_command(["test"])
        .with_env("APP_URL", f"http://host.docker.internal:{APPLICATION_PORT}")
        .with_volume_mapping(specmatic_yaml_path, "/usr/src/app/specmatic.yaml", mode="ro")
        .with_volume_mapping(build_reports_path, "/usr/src/app/build/reports/specmatic", mode="rw")
        .with_kwargs(extra_hosts={"host.docker.internal": "host-gateway"})
        .waiting_for(LogMessageWaitStrategy("Tests run:"))
    )
    container.start()
    thread = stream_container_logs(container, name="specmatic-test")
    yield container
    container.stop()
    thread.join()


@pytest.mark.skipif(
    os.environ.get("CI") == "true" and not sys.platform.startswith("linux"),
    reason="Run only on Linux CI; all platforms allowed locally",
)
def test_contract(api_service, mock_container, test_container):
    stdout, stderr = test_container.get_logs()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    if stderr or "Failures: 0" not in stdout:
        raise AssertionError(f"Contract tests failed; container logs:\n{stdout}\n{stderr}")  # noqa: EM102
