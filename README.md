# Specmatic FastAPI with Redis Demo

This is a Python implementation of the [Specmatic Order BFF Service](https://github.com/znsio/specmatic-order-ui)
project.  
The implementation is based on the [FastApi](https://fastapi.tiangolo.com/) framework.

The open api contract for the services is defined in
the [Specmatic Central Contract Repository](https://github.com/znsio/specmatic-order-contracts/blob/main/in/specmatic/examples/store/api_order_v1.yaml)

The bff service internally calls the order api service (on port 8080).

We also have a RedisService which connects to a Redis server  and performs a few common operations.

The purpose of this project is to:
1. Demonstrate how specmatic can be used to validate the contract of the bff service
while mocking out the order api service at the same time.

2. Demonstrate how to mock out the Redis server using Specmatic Redis Mock and Test Containers.


## Prerequisites

- Python 3.11+ 
- JRE 17+. 

1. Create a virtual environment and install all dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Running the contract suite

Run the tests using pytest:

```bash
pytest tests -v -s
```

## Setting test data for Specmatic Redis
Specmatic Redis takes an argument 'data' which is expected to be a directory with test data json files. 
The test data files are expected to have this structure:

```
    {
    "http-request": {
        "method": "POST",
        "path": "/redis",
        "body": {
            "operation": "get",
            "params": ["my_key"]
        }
    },
    "http-response": {
        "status": 200,
        "body": {
            "type": "string",
            "value": "HELLO"
        }
    }
}
```

**NOTE:** The operation value (ex: `get`) must be in lowercase.

## Running Specmatic Redis in Tests (with Testcontainers)

Use the containerized Specmatic Redis Mock to spin up an ephemeral Redis-like mock for your tests. The snippet below starts the image, mounts your test data, exposes the port, and **waits until the mock is ready** (detected via a log line) before the test proceeds.

```python
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy


SPECMATIC_REDIS_VERSION = "latest"  # or a pinned version like "0.9.4"
REDIS_HOST = "0.0.0.0"
REDIS_PORT = 6379
TEST_DATA_DIR = "/absolute/path/to/test/data"

container = (
    DockerContainer(f"specmatic/specmatic-redis:{SPECMATIC_REDIS_VERSION}")
    .with_command(f"virtualize --host {REDIS_HOST} --port {REDIS_PORT} --data {TEST_DATA_DIR}")
    .with_exposed_ports(REDIS_PORT)
    .with_volume_mapping(TEST_DATA_DIR, TEST_DATA_DIR)
    .waiting_for(LogMessageWaitStrategy(r"Specmatic Redis has started on .*:\d+").with_startup_timeout(10))
)
```

### What this does

* **Image**: `specmatic/specmatic-redis:{SPECMATIC_REDIS_VERSION}` – pulls and runs the Specmatic Redis Mock.
* **Command**: `virtualize --host ... --port ... --data ...` – launches Specmatic Redis and points it to your **test dataset** (files that define responses/fixtures).
* **Port exposure**: `.with_exposed_ports(REDIS_PORT)` – publishes the Redis port to the host so your test client can connect.
* **Volume mapping**: `.with_volume_mapping(TEST_DATA_DIR, TEST_DATA_DIR)` – mounts your local test data directory into the container at the **same** path (keeps file references simple).
* **Readiness check**: `LogMessageWaitStrategy(...)` – blocks test execution until the container logs the **ready** line.

### Readiness log pattern

The regex `r"Specmatic Redis has started on .*:\d+"` matches a line like:

```
Specmatic Redis has started on 0.0.0.0:6379
```

Ensure `TEST_DATA_DIR` is an **absolute path** and contains your test data files.


## Running Contract Tests
Here’s a clean, professional README-ready write-up you can use to document that block of code:

---

## 🧪 Running Contract Tests with Specmatic (FastAPI Example)

This section demonstrates how to **run contract tests** for a FastAPI application using [Specmatic](https://specmatic.io/).
Specmatic validates your app against its **OpenAPI contracts** and provides **API coverage reporting** and **mock interactions** for end-to-end testing.

```python
import os
from specmatic.core.specmatic import Specmatic
from definitions import ROOT_DIR
from app.main import app as fastapi_app

APP_HOST = "127.0.0.1"
APP_PORT = 8000

MOCK_HOST = "127.0.0.1"
MOCK_PORT = 8080
TEST_DATA_DIR = ROOT_DIR + "tests/contract/data"

SPECMATIC_CONFIG_FILE_PATH = ROOT_DIR + '/specmatic.yaml'

os.environ["SPECMATIC_GENERATIVE_TESTS"] = "true"


class TestContract:
    pass


(
    Specmatic()
    .with_specmatic_config_file_path(SPECMATIC_CONFIG_FILE_PATH)
    .with_stub(MOCK_HOST, MOCK_PORT, args=[f"--data={TEST_DATA_DIR}"])
    .with_asgi_app('app.main:app', APP_HOST, APP_PORT)
    .test_with_api_coverage_for_fastapi_app(TestContract, fastapi_app)
    .run()
)

os.environ["SPECMATIC_GENERATIVE_TESTS"] = "false"
```

---

### ⚙️ What This Does

| Step                               | Description                                                                                                                                                                                                                            |
|------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Environment setup**              | Defines the host and port for both the **FastAPI app** and the **Specmatic mock**. The mock uses data from `tests/contract/data` to simulate downstream dependencies.                                                                  |
| **Specmatic configuration**        | Points to your central `specmatic.yaml` file, which defines service contracts and dependencies.                                                                                                                                        |
| **Generative tests mode**          | Enables Specmatic’s *generative testing* mode (`SPECMATIC_GENERATIVE_TESTS=true`) to generate resilience tests.                                                                                                                        |
| **ASGI app registration**          | `.with_asgi_app('app.main:app', APP_HOST, APP_PORT)` registers your FastAPI app for validation. Here, `app.main:app` refers to the `app` object inside the `main.py` module.                                                           |
| **Mock registration**              | `.with_stub(MOCK_HOST, MOCK_PORT, args=[f"--data={TEST_DATA_DIR}"])` launches the Specmatic mock locally to serve mock responses from the specified test data directory.                                                               |
| **Contract testing with coverage** | `.test_with_api_coverage_for_fastapi_app(TestContract, fastapi_app)` runs Specmatic tests against your FastAPI app and reports API coverage by spinning up a lightweight coverage server (which parts of the contract were exercised). |
| **Clean-up**                       | Once the tests complete, the environment variable is reset to disable generative testing.                                                                                                                                              |

---

### 🧩 Typical Workflow

1. Ensure your `specmatic.yaml` file points to the correct contract specs.
2. Place your test data files under:

   ```
   tests/contract/data/
   ```
3. Specmatic will:

   * Start the mock server.
   * Boot your FastAPI app.
   * Execute contract-based test cases.
   * Report mismatches and coverage results.
---

### 🧠 Notes
* `app.main:app` follows the same syntax as `uvicorn main:app` — it references the `app` object defined inside `main.py`.
* `SPECMATIC_GENERATIVE_TESTS=true` enables generation of resilience tests.
* Keep `TEST_DATA_DIR` paths **absolute** to avoid issues with volume mounts or relative references.
* API coverage output helps ensure all contract endpoints are implemented and validated.
---


