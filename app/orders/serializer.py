from typing import List

from fastapi import Depends

from app.orders.models import Order
from app.orders.schemas import OrdersResponse, OrderResponse, DocumentResponse, Pagination
from app.users.repositories.user import UserRepository
from app.users.schemas import UserFullResponse


class OrderSerializer:

    def __init__(self, user_repository: UserRepository = Depends()):
        self.user_repository = user_repository

    async def get_order_response(self, order: Order) -> OrderResponse:
        customer = await self.user_repository.get_user_by_id(order.customer)
        expert = await self.user_repository.get_user_by_id(order.expert)
        return OrderResponse(
            id=str(order.id),
            name=order.name,
            description=order.description,
            status=order.status,
            rating=order.rating,
            customer=UserFullResponse.from_model(customer) if customer else None,
            expert=UserFullResponse.from_model(expert) if expert else None,
            document=DocumentResponse.from_model(order.document) if order.document else None,
        )

    async def get_orders_response(
            self,
            orders: List[Order],
            total: int,
            limit: int,
            offset: int,
    ) -> OrdersResponse:
        return OrdersResponse(
            items=[await self.get_order_response(order) for order in orders],
            pagination=Pagination(
                offset=offset,
                limit=limit,
                total=total,
            ),
        )
