from fastapi import APIRouter, Depends

from ..schemas import Order
from ..request_guards import require_json_body
from ..services import OrdersService

orders = APIRouter()


@orders.post("/orders", status_code=201, dependencies=[Depends(require_json_body)])
async def create_order(order: Order) -> dict[str, int]:
    new_order = await OrdersService.create_order(order)
    return {"id": new_order["id"]}
