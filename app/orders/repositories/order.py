from typing import List, Optional

from bson import ObjectId

from app.core.database import PydanticObjectId
from app.core.enums import Collection
from app.core.repository import BaseRepository
from app.orders.enums import OrderStatus, FileType
from app.orders.models import Order
from app.orders.schemas import CreateOrderDTO, FileInfoDTO
from app.users.models import User


class OrderRepository(BaseRepository):
    collection_name: Collection = Collection.ORDERS

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        order = await self._db.find_one({"_id": ObjectId(order_id)})
        return Order(**order) if order else None

    async def get_published_orders(
            self,
            limit: int,
            offset: int,
    ) -> (int, List[Order]):
        cursor = self._db.aggregate([
            {"$match": {"status": OrderStatus.published}},
            {"$skip": offset},
            {"$limit": limit},
        ])
        orders = [Order(**x) async for x in cursor]
        total = await self._db.count_documents({})
        return total, orders

    async def get_self_orders(
            self,
            user: User,
            limit: int,
            offset: int,
            statuses: List[OrderStatus],
    ) -> (int, List[Order]):
        conditions = {"$or": [
            {"customer": str(user.id)},
            {"expert": str(user.id)},
        ]}
        if statuses:
            conditions["status"] = {"$in": statuses}
        cursor = self._db.aggregate([
            {"$match": conditions},
            {"$skip": offset},
            {"$limit": limit},
        ])
        orders = [Order(**x) async for x in cursor]
        total = await self._db.count_documents(conditions)
        return total, orders

    async def create_order(self, order: CreateOrderDTO, user: User) -> Order:
        insert_result = await self._db.insert_one(
            Order(
                customer=str(user.id),
                name=order.name,
                description=order.description
            ).dict(exclude_none=True)
        )
        inserted_order = await self._db.find_one({"_id": insert_result.inserted_id})
        return Order(**inserted_order)

    async def change_oder_status(self, order_id: str, status: OrderStatus) -> Order:
        await self._db.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": status}})
        return Order(**await self._db.find_one({"_id": ObjectId(order_id)}))

    async def set_expert(self, order_id: str, expert_id: str) -> Order:
        await self._db.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": OrderStatus.handling, "expert": expert_id}})
        return Order(**await self._db.find_one({"_id": ObjectId(order_id)}))

    async def set_rating(self, order_id: str, rating: float) -> Order:
        await self._db.update_one({"_id": ObjectId(order_id)}, {"$set": {"rating": rating}})
        return Order(**await self._db.find_one({"_id": ObjectId(order_id)}))

    async def set_document_text(self, order_id: str, text: str):
        await self._db.update_one({"_id": ObjectId(order_id)}, {"$set": {"document.text": text}})

    async def add_file_to_order_input(self, order_id: str, file: FileInfoDTO) -> Order:
        order_id = PydanticObjectId(order_id)
        if file.file_type == FileType.img:
            setter = {"$push": {"document.input.images": file.file_link}}
        else:
            setter = {"$set": {"document.input.file": file.file_link}}
        await self._db.update_one(
            {"_id": order_id},
            setter,
        )
        updated_order = await self._db.find_one({"_id": order_id})
        return Order(**updated_order)

    async def add_file_to_order_result(self, order_id: str, file: FileInfoDTO) -> Order:
        order_id = PydanticObjectId(order_id)
        if file.file_type == FileType.img:
            setter = {"$push": {"document.result.images": file.file_link}}
        else:
            setter = {"$set": {"document.result.file": file.file_link}}
        await self._db.update_one(
            {"_id": order_id},
            setter,
        )
        updated_order = await self._db.find_one({"_id": order_id})
        return Order(**updated_order)
