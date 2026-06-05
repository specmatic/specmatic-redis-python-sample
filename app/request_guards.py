from fastapi import HTTPException, Request


async def require_json_body(request: Request) -> None:
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type != "application/json":
        raise HTTPException(status_code=415, detail="Request body is required")

    if not await request.body():
        raise HTTPException(status_code=415, detail="Request body is required")
