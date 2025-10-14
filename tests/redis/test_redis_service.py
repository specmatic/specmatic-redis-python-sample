import logging

import pytest
from redis import Redis
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy, CompositeWaitStrategy

from app.redis_service import RedisService
from definitions import ROOT_DIR

REDIS_HOST = "0.0.0.0"
REDIS_PORT = 6379
STUB_DATA_DIR = ROOT_DIR + "/tests/redis/data"

logger = logging.getLogger("specmatic.redis.mock")
logger.setLevel(logging.DEBUG)


class TestRedisService:

    @pytest.fixture(scope="module")
    def redis_service(self):
        container = (
            DockerContainer("specmatic/specmatic-redis:latest")
            .with_command(f"virtualize --host {REDIS_HOST} --port {REDIS_PORT} --data {STUB_DATA_DIR}")
            .with_exposed_ports(REDIS_PORT)
            .with_volume_mapping(STUB_DATA_DIR, STUB_DATA_DIR)
            .waiting_for(LogMessageWaitStrategy(r"Specmatic Redis has started on .*:\d+"))
        )

        redis_client = None

        try:
            container.start()
            print_container_logs(container)
            port = container.get_exposed_port(REDIS_PORT)
            redis_client = Redis(host=REDIS_HOST, port=port, decode_responses=True)
            service = RedisService(redis_client)
            yield service

        except Exception as exc:
            pytest.fail(f"Unable to start Specmatic Redis: {exc}")

        finally:
            if redis_client is not None:
                redis_client.close()
            container.stop()

    def test_get_value(self, redis_service):
        assert redis_service.get_value("my_key") == "HELLO"

    def test_queue_lpop(self, redis_service):
        assert redis_service.lpop("my_queue") == "ORDER_1"


def print_container_logs(container):
    stdout, stderr = container.get_logs()
    logger.info("=== STDOUT ===")
    logger.info(stdout.decode("utf-8"))
    logger.info("=== STDERR ===")
    logger.info(stderr.decode("utf-8"))
