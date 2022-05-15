from typing import Optional

from bson.objectid import ObjectId as BsonObjectId
from motor.motor_asyncio import AsyncIOMotorClient


__all__ = ["get_database", "get_test_database", "AsyncIOMotorClient", "PydanticObjectId"]

from app.settings import settings

mongo_client: Optional[AsyncIOMotorClient] = None


async def get_database() -> AsyncIOMotorClient:
    return mongo_client[settings.MONGO_INITDB_DATABASE]


async def get_test_database() -> AsyncIOMotorClient:
    return mongo_client[settings.TEST_MONGO_INITDB_DATABASE]


class PydanticObjectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, BsonObjectId):
            raise TypeError('ObjectId required')
        return str(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")
