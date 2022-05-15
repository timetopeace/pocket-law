from fastapi import status

from app.core.exception.base import AppBaseException, ErrorDescription
from app.core.exception.error_codes import invalid_code, user_already_exists, invalid_email_or_password, \
    email_not_confirmed, user_without_password, invalid_confirm_email, user_not_found


class InvalidCodeException(AppBaseException):
    _status_code = status.HTTP_404_NOT_FOUND
    _code = invalid_code
    _description = ErrorDescription(en="Invalid code", ru="Неверный код")


class UserAlreadyExistsException(AppBaseException):
    _status_code = status.HTTP_400_BAD_REQUEST
    _code = user_already_exists
    _description = ErrorDescription(
        en="A user with that username already exists. Proceed to login screen",
        ru="Пользователь с таким email уже существует. Перейдите на страницу авторизации"
    )


class InvalidEmailOrPasswordException(AppBaseException):
    _status_code = status.HTTP_401_UNAUTHORIZED
    _code = invalid_email_or_password
    _description = ErrorDescription(en="Your email and/or password do not match", ru="Неверный email или пароль")


class EmailNotConfirmedException(AppBaseException):
    _status_code = status.HTTP_401_UNAUTHORIZED
    _code = email_not_confirmed
    _description = ErrorDescription(
        en="Please verify your email by following the link we have sent to your email address",
        ru="Пожалуйста, подтвердите свою почту, для этого пройдите по ссылке в письме, которое мы отправили ранее"
    )


class UserWithoutPasswordException(AppBaseException):
    _status_code = status.HTTP_401_UNAUTHORIZED
    _code = user_without_password
    _description = ErrorDescription(
        en='The password for this user isn\'t set. Please click "I forgot my password"',
        ru='Пароль для данного пользователя не установлен. Нажмите "Я не помню пароль"'
    )


class InvalidConfirmEmailException(AppBaseException):
    _status_code = status.HTTP_400_BAD_REQUEST
    _code = invalid_confirm_email
    _description = ErrorDescription(
        en="Invalid request",
        ru="Неверный запрос"
    )


class UserNotFoundException(AppBaseException):
    _status_code = status.HTTP_404_NOT_FOUND
    _code = user_not_found
    _description = ErrorDescription(en="User not found", ru="Пользователь не найден")
