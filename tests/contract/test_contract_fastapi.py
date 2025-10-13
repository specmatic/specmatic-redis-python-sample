import os

import pytest

from specmatic.core.specmatic import Specmatic
from definitions import ROOT_DIR

from app import app as fastapi_app

APP_HOST = "127.0.0.1"
APP_PORT = 8000

STUB_HOST = "127.0.0.1"
STUB_PORT = 8080
STUB_DATA_DIR = ROOT_DIR + "tests/contract/data"

SPECMATIC_CONFIG_FILE_PATH = ROOT_DIR + '/specmatic.yaml'

os.environ["SPECMATIC_GENERATIVE_TESTS"] = "true"


class TestContract:
    pass


(
    Specmatic()
    .with_specmatic_config_file_path(str(SPECMATIC_CONFIG_FILE_PATH))
    .with_project_root(str(ROOT_DIR))
    .with_stub(
        STUB_HOST,
        STUB_PORT,
        args=[f"--data={STUB_DATA_DIR}"]
    ).with_asgi_app('app:app', APP_HOST, APP_PORT)
    .test_with_api_coverage_for_fastapi_app(
        TestContract, fastapi_app
    ).run()
)

os.environ["SPECMATIC_GENERATIVE_TESTS"] = "false"

if __name__ == "__main__":
    pytest.main()
