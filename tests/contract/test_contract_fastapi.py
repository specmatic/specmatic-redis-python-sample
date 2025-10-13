import os
import pytest

from specmatic.core.specmatic import Specmatic
from definitions import ROOT_DIR

from app import app as fastapi_app

APP_HOST = "127.0.0.1"
APP_PORT = 8000
STUB_HOST = "127.0.0.1"
STUB_PORT = 8080
SPECMATIC_CONFIG_FILE_PATH = ROOT_DIR + '/specmatic.yaml'
expectation_json_file = ROOT_DIR + '/tests/data/stub_products_200.json'

os.environ["SPECMATIC_GENERATIVE_TESTS"] = "true"


class TestContract:
    pass


(
    Specmatic()
    .with_specmatic_config_file_path(SPECMATIC_CONFIG_FILE_PATH)
    .with_project_root(ROOT_DIR)
    .with_stub(
        STUB_HOST, STUB_PORT, [expectation_json_file]
    ).with_asgi_app('app:app', APP_HOST, APP_PORT)
    .test_with_api_coverage_for_fastapi_app(
        TestContract, fastapi_app
    ).run()
)

os.environ["SPECMATIC_GENERATIVE_TESTS"] = "false"

if __name__ == "__main__":
    pytest.main()
