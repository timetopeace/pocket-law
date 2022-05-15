from fastapi import status

from app.core.exception.base import AppBaseException
from app.core.exception.base import ErrorDescription
from app.core.exception.error_codes import smsc_error


class SMSCError(AppBaseException):
    _status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    _code = smsc_error
    _description = ErrorDescription(
        en="Unexpected SMSC API error",
        ru="SMS сервис недоступен",
    )
