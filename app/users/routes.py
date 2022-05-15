from fastapi import APIRouter, Depends, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT

from app.core.security import generate_code, verify_password
from app.services.mail_service.mail_service import MailService
from app.services.sms_service.sms_service import SMSService
from app.users.auth import get_current_user
from app.users.enums import UserRole
from app.users.exceptions import InvalidCodeException, UserAlreadyExistsException, InvalidEmailOrPasswordException, \
    UserWithoutPasswordException, EmailNotConfirmedException, InvalidConfirmEmailException, UserNotFoundException
from app.users.models import User
from app.users.repositories.exceptions import UserInDBAlreadyExistsException, UserInDBNotFoundException
from app.users.repositories.user import UserRepository
from app.users.schemas import (
    UserFullResponse,
    CustomerSignin,
    AuthTokens,
    CreateExpertDTO,
    ExpertResponse,
    ExpertSignin,
    VerifyEmail,
    RefreshRequest,
    UpdateUserDTO,
    UpdateUserRequest,
    CustomerAuthResponse,
    CustomerAuthRequest,
)

user_router = APIRouter(tags=['user'], prefix="/user")


@user_router.get(
    path="/",
    response_model=UserFullResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def get_current_user_profile(
        user: User = Depends(get_current_user),
) -> UserFullResponse:
    return UserFullResponse.from_model(user)


@user_router.post("/auth/customer/", response_description="Customer authorize", response_model=CustomerAuthResponse)
async def auth_customer(
        background_tasks: BackgroundTasks,
        sms_service: SMSService = Depends(),
        user_auth: CustomerAuthRequest = Body(...),
        user_repository: UserRepository = Depends(UserRepository),
):
    user, created = await user_repository.get_or_create_user_by_phone(phone=user_auth.phone)
    background_tasks.add_task(sms_service.send_sms, user.phone, generate_code())
    return CustomerAuthResponse(
        data="Код для входа был отправлен по смс",
        created=created,
    )


@user_router.post("/signin/customer/", response_description="Customer signin/signup", response_model=AuthTokens)
async def signin_customer(
        user_signin: CustomerSignin = Body(...),
        Authorize: AuthJWT = Depends(),
        user_repository: UserRepository = Depends(UserRepository),
):
    user = await user_repository.get_user_by_phone(phone=user_signin.phone)
    if not user:
        raise UserNotFoundException()

    if user.acl.code != user_signin.code:
        raise InvalidCodeException()

    return {
        "access_token": Authorize.create_access_token(subject=user.phone),
        "refresh_token": await user_repository.add_refresh_token(phone=user.phone)
    }


@user_router.post("/signup/expert/", response_description="Expert signup", response_model=ExpertResponse)
async def create_expert(
        background_tasks: BackgroundTasks,
        mail_service: MailService = Depends(),
        user_signup: CreateExpertDTO = Body(...),
        user_repository: UserRepository = Depends(UserRepository),
):
    try:
        new_user = await user_repository.create_expert(user_signup)
    except UserInDBAlreadyExistsException:
        raise UserAlreadyExistsException()

    background_tasks.add_task(mail_service.send_verification_message, new_user.email.value, new_user.email.accept)

    return ExpertResponse.from_model(user=new_user)


@user_router.post("/signin/expert/", response_description="Expert signin", response_model=AuthTokens)
async def signin_expert(
        user_signin: ExpertSignin = Body(...),
        Authorize: AuthJWT = Depends(),
        user_repository: UserRepository = Depends(UserRepository),
):
    user = await user_repository.get_user_by_email(user_signin.email)
    if not user:
        raise InvalidEmailOrPasswordException()
    if not user.acl or not user.acl.password.hash:
        raise UserWithoutPasswordException()
    elif not user.email.confirmed:
        raise EmailNotConfirmedException()

    if not verify_password(user_signin.password, user.acl.password.hash):
        raise InvalidEmailOrPasswordException()

    return {
        "access_token": Authorize.create_access_token(subject=user.email.value),
        "refresh_token": await user_repository.add_refresh_token(email=user.email.value)
    }


@user_router.get("/register-confirm/{code}/", response_description="Email confirmation")
async def email_verification(
        code: str,
        user_repository: UserRepository = Depends(),
        # code: VerifyEmail = Body(...)
):
    try:
        await user_repository.confirm_email_by_code(code)
    except UserInDBNotFoundException:
        raise InvalidConfirmEmailException()
    return JSONResponse(content={"data": "Email подтвержден"})


@user_router.post("/token/refresh/", response_description="Refresh a session token", response_model=AuthTokens)
async def refresh_token(
        refresh_token: RefreshRequest = Body(...),
        Authorize: AuthJWT = Depends(),
        user_repository: UserRepository = Depends(UserRepository),
):
    try:
        user = await user_repository.get_by_refresh_token(refresh_token.refresh_token)
    except UserInDBNotFoundException:
        raise UserNotFoundException()

    if user.md.role == UserRole.customer:
        access_token = Authorize.create_access_token(subject=user.phone)
    else:
        access_token = Authorize.create_access_token(subject=user.email.value)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token.refresh_token
    }


@user_router.post(
    path="/",
    response_description="Update profile",
    response_model=UserFullResponse,
    response_model_exclude_none=True,
)
async def update_user(
        user: User = Depends(get_current_user),
        user_repository: UserRepository = Depends(),
        update_user_request: UpdateUserRequest = Body(...),
):
    user = await user_repository.update_user(
        user=user,
        user_dto=UpdateUserDTO(**update_user_request.dict(exclude_none=True))
    )
    return UserFullResponse.from_model(user).dict(exclude_none=True, by_alias=True)
