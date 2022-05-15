import re
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.core.database import PydanticObjectId
from app.core.enums import Collection
from app.core.repository import BaseRepository
from app.core.security import get_refresh_token, get_password_hash
from app.users.enums import UserRole
from app.users.models import User, UserMD, UserEmail, UserACL, ACLPassword
from app.users.repositories.exceptions import UserInDBAlreadyExistsException, UserInDBNotFoundException
from app.users.schemas import CreateExpertDTO, UpdateUserDTO


class UserRepository(BaseRepository):
    collection_name: Collection = Collection.USERS

    async def get_user_by_email(
            self,
            email: str,
    ) -> Optional[User]:
        user_row = await self._db.find_one(
            {"email.value": re.compile(email, re.IGNORECASE)}
        )
        if not user_row:
            return None
        return User(**user_row)

    async def get_user_by_phone(
            self,
            phone: str,
    ) -> Optional[User]:
        user_row = await self._db.find_one(
            {"phone": phone}
        )
        if not user_row:
            return None
        return User(**user_row)

    async def update_user_code(self, phone: str, code: str):
        await self._db.update_one({"phone": phone}, {"$set": {"acl.code": code}})

    async def get_or_create_user_by_phone(self, phone: str) -> (User, bool):
        created = False
        user = await self.get_user_by_phone(phone)
        if not user:
            user = await self._db.insert_one(
                User(
                    _id=PydanticObjectId(),
                    phone=phone,
                    md=UserMD(
                        lmt=int(datetime.utcnow().timestamp()),
                        ect=int(datetime.utcnow().timestamp()),
                        role=UserRole.customer,
                    )
                ).dict(exclude_none=True)
            )
            user = await self._db.find_one({"_id": user.inserted_id})
            user = User(**user)
            created = True
        return user, created

    async def add_refresh_token(self, phone: Optional[str] = None, email: Optional[str] = None) -> str:
        if not phone and not email:
            raise Exception
        refresh_token = get_refresh_token()
        await self._db.update_one(
            {"$or": [
                {"email.value": email},
                {"phone": phone},
            ]},
            {"$push": {"tokens": {"value": refresh_token}}},
        )
        return refresh_token

    async def create_expert(self, user_data: CreateExpertDTO) -> User:
        user = await self.get_user_by_email(user_data.email)
        if user:
            raise UserInDBAlreadyExistsException()

        user = await self._db.insert_one(
            User(
                name=user_data.name,
                email=UserEmail(value=user_data.email, accept=str(uuid4())),
                acl=UserACL(
                    password=ACLPassword(hash=get_password_hash(user_data.password))
                ),
                md=UserMD(
                    lmt=int(datetime.utcnow().timestamp()),
                    ect=int(datetime.utcnow().timestamp()),
                    role=UserRole.expert,
                ),
            ).dict()
        )
        new_user = await self._db.find_one({"_id": user.inserted_id})
        return User(**new_user)

    async def confirm_email_by_code(self, code: str) -> User:
        user = await self._db.find_one({"email.accept": code})
        if not user:
            raise UserInDBNotFoundException()
        await self._db.update_one(
            {"email.accept": code}, {"$set": {"email.confirmed": True}}
        )
        return User(**user)

    async def get_by_refresh_token(self, token: str) -> Optional[User]:
        user_row = await self._db.find_one({"tokens": {"$elemMatch": {"value": token}}})

        if not user_row:
            raise UserInDBNotFoundException()
        return User(**user_row)

    async def update_user(
            self,
            user: User,
            user_dto: UpdateUserDTO,
    ):
        update_dict = user_dto.dict(exclude_unset=True)
        if "name" in update_dict:
            user.name = user_dto.name
        if "phone" in update_dict:
            user.phone = user_dto.phone
        if "email" in update_dict:
            user.email.value = user_dto.email
        if "rating" in update_dict:
            user.rating = user_dto.rating
        await self._db.update_one(
            {"_id": PydanticObjectId(user.id)}, {"$set": user.dict()}
        )
        updated_user = await self._db.find_one({"_id": PydanticObjectId(user.id)})
        return User(**updated_user)
