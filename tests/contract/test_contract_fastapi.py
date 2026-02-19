import os

import pytest

from specmatic.core.specmatic import Specmatic
from definitions import PROJECT_ROOT

from app.main import app as fastapi_app

APP_HOST = "127.0.0.1"
APP_PORT = 8000


class TestContract:
    pass


(
    Specmatic(PROJECT_ROOT)
    .with_mock()
    .with_asgi_app('app.main:app', APP_HOST, APP_PORT)
    .test_with_api_coverage_for_fastapi_app(TestContract, fastapi_app)
    .run()
)

if __name__ == "__main__":
    pytest.main()
