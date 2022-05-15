from fastapi import Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import JWTDecodeError, MissingTokenError

from app.users.models import User
from app.users.repositories.user import UserRepository


async def _get_user(
    user_repository: UserRepository = Depends(UserRepository),
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
#
#
# async def get_current_active_user(
#     current_user: User = Depends(_get_user),
# ) -> User:
#     if not current_user.email.confirmed:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not active"
#         )
#     return current_user
#
#
#
#
# async def get_user_or_none(
#     user_repository: UserRepository = Depends(UserRepository),
#     Authorize: AuthJWT = Depends(),
# ) -> Union[User, None]:
#     """
#     Return the current active user if is present (using the token Bearer) or None
#     """
#     try:
#         Authorize.jwt_required()
#         user_email = Authorize.get_jwt_subject()
#     except JWTDecodeError as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=e.message,
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     except MissingTokenError as e:
#         return None
#
#     user = await user_repository.get_user_by_email(user_email)
#     return user
