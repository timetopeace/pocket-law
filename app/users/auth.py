from fastapi import Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import JWTDecodeError, MissingTokenError

from app.users.enums import UserRole
from app.users.models import User
from app.users.repositories.user import UserRepository


async def _get_user(
    user_repository: UserRepository = Depends(),
    authorize: AuthJWT = Depends(),
) -> User:
    try:
        authorize.jwt_required()
        subject = authorize.get_jwt_subject()
    except JWTDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except MissingTokenError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        int(subject)
    except ValueError:
        user = await user_repository.get_user_by_email(subject)
    else:
        user = await user_repository.get_user_by_phone(subject)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not exists")

    return user


async def get_current_user(
        current_user: User = Depends(_get_user),
) -> User:
    return current_user


async def get_expert(
        current_user: User = Depends(_get_user),
) -> User:
    if not current_user.md.role == UserRole.expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only for experts"
        )
    return current_user


async def get_customer(
        current_user: User = Depends(_get_user),
) -> User:
    if not current_user.md.role == UserRole.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only for customers"
        )
    return current_user
