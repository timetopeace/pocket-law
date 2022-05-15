from typing import Optional, Type

from pydantic import Field
from pydantic.main import BaseModel


class TokenResponse(BaseModel):
    token: str
    exp: Optional[int]
    iat: Optional[int]
    refresh_token: str = Field(..., alias='refreshToken')
    user_id: Optional[str] = Field(None, alias='userId')

    @classmethod
    def from_db(cls: Type[BaseModel], token, exp, iat, refresh_token):
        return cls(
            token=token,
            ext=exp,
            iat=iat,
            refreshToken=refresh_token
        )
