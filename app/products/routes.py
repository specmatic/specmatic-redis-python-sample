from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from ..schemas import Product, ProductType
from ..request_guards import require_json_body
from ..services import ProductService

products = APIRouter()


@products.get("/findAvailableProducts")
async def find_available_products(
    type: ProductType | None = None, pageSize: int = Header(default=None)
):
    if not pageSize:
        raise HTTPException(400, "pageSize is required")

    # NOTE: API_SPEC v4 requires expects TIMEOUT when type="other" or pageSize=20
    if type == ProductType.OTHER or pageSize == 20:
        raise HTTPException(503, "Timeout")

    products = await ProductService.find_products(type)
    return JSONResponse(content=products)


@products.post("/products", status_code=201, dependencies=[Depends(require_json_body)])
async def add_product(data: Product) -> dict[str, int]:
    product = await ProductService.create_product(data)
    return {"id": product["id"]}
