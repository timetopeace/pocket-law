from abc import ABCMeta, abstractmethod
from typing import Type

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import AsyncIOMotorClient, get_database
from app.core.enums import Collection


class BaseRepository(metaclass=ABCMeta):

    def __init__(self, db: AsyncIOMotorClient = Depends(get_database)):
        if not isinstance(self.collection_name, Collection):
            raise RuntimeError('Unsupported collection name')
        self._db: AsyncIOMotorCollection = db[self.collection_name.value]

    @property
    @abstractmethod
    def collection_name(self) -> Type[Collection]:
        pass

    async def drop(self):
        await self._db.drop()
