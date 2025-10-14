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
while stubbing out the order api service at the same time.

2. Demonstrate how to stub out the Redis server using Specmatic Redis and Test Containers.


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

## Setting stubs for Specmatic Redis
Specmatic Redis takes an argument 'data' which is expected to be a directory with stub json files. 
The stub files are expected to have this structure:

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

**NOTE:** The operation value must be in lowercase.

## Running Specmatic Redis in Tests (with Testcontainers)

Use the containerized Specmatic Redis Mock to spin up an ephemeral Redis-like stub for your tests. The snippet below starts the image, mounts your stub data, exposes the port, and **waits until the mock is ready** (detected via a log line) before the test proceeds.

```python
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy


SPECMATIC_REDIS_VERSION = "latest"  # or a pinned version like "0.9.4"
REDIS_HOST = "0.0.0.0"
REDIS_PORT = 6379
STUB_DATA_DIR = "/absolute/path/to/test/data"

container = (
    DockerContainer(f"specmatic/specmatic-redis:{SPECMATIC_REDIS_VERSION}")
    .with_command(f"virtualize --host {REDIS_HOST} --port {REDIS_PORT} --data {STUB_DATA_DIR}")
    .with_exposed_ports(REDIS_PORT)
    .with_volume_mapping(STUB_DATA_DIR, STUB_DATA_DIR)
    .waiting_for(LogMessageWaitStrategy(r"Specmatic Redis has started on .*:\d+").with_startup_timeout(10))
)
```

### What this does

* **Image**: `specmatic/specmatic-redis:{SPECMATIC_REDIS_VERSION}` – pulls and runs the Specmatic Redis Mock.
* **Command**: `virtualize --host ... --port ... --data ...` – launches Specmatic Redis and points it to your **stub dataset** (files that define responses/fixtures).
* **Port exposure**: `.with_exposed_ports(REDIS_PORT)` – publishes the Redis port to the host so your test client can connect.
* **Volume mapping**: `.with_volume_mapping(STUB_DATA_DIR, STUB_DATA_DIR)` – mounts your local stub directory into the container at the **same** path (keeps file references simple).
* **Readiness check**: `LogMessageWaitStrategy(...)` – blocks test execution until the container logs the **ready** line.

### Readiness log pattern

The regex `r"Specmatic Redis has started on .*:\d+"` matches a line like:

```
Specmatic Redis has started on 0.0.0.0:6379
```

Ensure `STUB_DATA_DIR` is an **absolute path** and contains your stub files.
