# Specmatic FastAPI Demo

This project wires the FastAPI sample that ships with [`specmatic-python-extensions`](../specmatic-python-extensions) into its own runnable contract-test harness. The application code in `app/` is copied verbatim from `specmatic-python-extensions/test/apps/fast_api`, and the Specmatic config (`specmatic.json`) is copied locally so it mirrors the upstream setup while continuing to reuse the expectation JSON files from that repository.

## Prerequisites

1. Create a virtual environment and install the demo plus Specmatic extensions:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e ../specmatic-python-extensions
   ```

2. Ensure this repository lives alongside `specmatic-python-extensions` (the paths above assume the common parent directory layout from the instructions).

## Running the contract suite

The contract test mirrors `test/asgi/test_contract_with_resilience_fastapi.py` from the extensions project. It starts:

- the Specmatic stub using `specmatic-python-extensions/specmatic.json`
- the copied FastAPI app under Uvicorn
- the generated contract & API coverage checks via `test_with_api_coverage_for_fastapi_app`

Execute the test with:

```bash
pytest tests/contract/test_contract_fastapi.py
```

The `.env` file (copied from the extensions project) points the FastAPI app to the stub (`ORDER_API_HOST=127.0.0.1`, `ORDER_API_PORT=8080`). The Specmatic stub is seeded with the same expectation JSON files from `specmatic-python-extensions/test/data`, so the behaviour matches the original sample exactly.

## Working with the app

Because the FastAPI code is reused as-is, you can run it directly too:

```bash
uvicorn app:app --reload
```

If you point it at a real downstream service instead of the Specmatic stub, update `ORDER_API_HOST`, `ORDER_API_PORT`, and `AUTH_TOKEN` as needed.
