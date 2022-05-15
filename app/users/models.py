from typing import Optional, List

from pydantic import Field
from pydantic.main import BaseModel

from app.core.database import PydanticObjectId
from app.users.enums import UserRole


class PasswordRecovery(BaseModel):
    code: Optional[str] = None
    exp: Optional[str] = None


class ACLPassword(BaseModel):
    hash: Optional[str] = None
    recovery: Optional[PasswordRecovery] = None


class UserACL(BaseModel):
    password: Optional[ACLPassword]
    code: Optional[int]


class UserMD(BaseModel):
    lmt: str
    ect: str
    role: UserRole


class UserEmail(BaseModel):
    value: str
    confirmed: bool = False
    accept: Optional[str] = None


class UserToken(BaseModel):
    value: str


class User(BaseModel):
    id: PydanticObjectId = Field(None, alias="_id")
    name: Optional[str]
    phone: Optional[str]
    email: Optional[UserEmail]
    acl: Optional[UserACL]
    tokens: List[UserToken] = Field([])
    rating: Optional[float]
    md: UserMD

    class Config:
        allow_population_by_field_name = True
