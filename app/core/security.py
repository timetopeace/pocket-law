import uuid

from passlib.context import CryptContext
from fastapi.security.api_key import APIKeyHeader
from app.settings import settings
from fastapi import Security, HTTPException, status


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_refresh_token():
    return str(uuid.uuid4())


api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=True)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == settings.API_KEY:
        return api_key_header
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
