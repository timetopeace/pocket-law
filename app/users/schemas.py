from typing import Optional, Type

from pydantic import root_validator
from pydantic.fields import Field
from pydantic.main import BaseModel

from app.users.enums import UserRole
from app.users.models import User, UserMD


class UserMDResponse(BaseModel):
    lmt: str
    ect: str
    role: UserRole

    @classmethod
    def from_model(cls: Type[BaseModel], model: UserMD):
        return cls(
            lmt=model.lmt,
            ect=model.ect,
            role=model.role,
        )


class UserFullResponse(BaseModel):
    id: str = Field(...)
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None
    md: Optional[UserMDResponse]

    @classmethod
    def from_model(cls: Type[BaseModel], user: User):
        return cls(
            id=str(user.id),
            name=user.name,
            phone=user.phone if user.phone else None,
            email=user.email.value if user.email and user.email.value else None,
            rating=user.rating,
            md=UserMDResponse.from_model(user.md)
        )


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None

    @root_validator(pre=True)
    def check_empty_body(cls, values):
        if not values:
            raise ValueError('Empty request body')
        return values


class UpdateUserDTO(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None


class CustomerResponse(BaseModel):
    id: str = Field(...)
    name: Optional[str] = None
    email: Optional[str] = None

    @classmethod
    def from_model(cls: Type[BaseModel], user: User):
        return cls(
            id=str(user.id),
            name=user.name,
            phone=user.phone,
        )


class ExpertResponse(BaseModel):
    id: str = Field(...)
    name: Optional[str] = None
    email: Optional[str] = None

    @classmethod
    def from_model(cls: Type[BaseModel], user: User):
        return cls(
            id=str(user.id),
            name=user.name,
            email=user.email.value,
        )


class CustomerSignin(BaseModel):
    phone: str
    code: int


class CustomerAuthRequest(BaseModel):
    phone: str


class CustomerAuthResponse(BaseModel):
    data: str
    created: bool


class CreateExpertDTO(BaseModel):
    name: str
    email: str
    password: str


class ExpertSignin(BaseModel):
    email: str
    password: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str


class VerifyEmail(BaseModel):
    code: str


class RefreshRequest(BaseModel):
    refresh_token: str
