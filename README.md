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
Specmatic Redis takes a command line argument which contains 