import logging

import pytest
from redis import Redis
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy, CompositeWaitStrategy

from app.redis_service import RedisService
from definitions import ROOT_DIR

logger = logging.getLogger("specmatic.redis.mock")
logger.setLevel(logging.DEBUG)

REDIS_HOST = "0.0.0.0"
REDIS_PORT = 6379
STUB_DATA_DIR = ROOT_DIR + "/tests/redis/data"


class TestRedisService:
    @pytest.fixture(scope="module")
    def redis_service(self):
        wait_strategy = CompositeWaitStrategy(
            LogMessageWaitStrategy(r"Specmatic Redis has started on .*:\d+")
        ).with_startup_timeout(30)
        container = (
            DockerContainer("specmatic/specmatic-redis:latest")
            .with_command(f"virtualize --host {REDIS_HOST} --port {REDIS_PORT} --data {STUB_DATA_DIR}")
            .with_exposed_ports(REDIS_PORT)
            .with_volume_mapping(STUB_DATA_DIR, STUB_DATA_DIR)
            .waiting_for(wait_strategy)
        )

        client: Redis | None = None
        started = False

        try:
            try:
                container.start()
                self.print_container_logs(container)
            except Exception as exc:
                pytest.skip(f"Unable to start container: {exc}")

            started = True
            port = container.get_exposed_port(REDIS_PORT)

            client = Redis(host=REDIS_HOST, port=port, decode_responses=True)
            service = RedisService(client)
            yield service
        finally:
            try:
                if started:
                    container.stop()
            finally:
                if client is not None:
                    client.close()

    def print_container_logs(self, container):
        stdout, stderr = container.get_logs()
        logger.info("=== STDOUT ===")
        logger.info(stdout.decode("utf-8"))
        logger.info("=== STDERR ===")
        logger.info(stderr.decode("utf-8"))

    def test_get_value(self, redis_service):
        assert redis_service.get_value("my_key") == "HELLO"

    def test_lpop(self, redis_service):
        assert redis_service.lpop("my_queue") == "ORDER_1"
