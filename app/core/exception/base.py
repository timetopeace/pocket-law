import logging
from typing import Optional
from pydantic.main import BaseModel

from fastapi import HTTPException


class ErrorDescription(BaseModel):
    ru: str
    en: str


class AppBaseException(Exception):
    _status_code: int
    _code: int
    _description: ErrorDescription
    _logger = logging.getLogger(__name__)

    def __new__(cls):
        cls._logger.error(cls._get_message())
        return HTTPException(status_code=cls._get_status_code(), detail=cls._get_message())

    @classmethod
    def _get_message(cls):
        return {"code": cls._code, "description": cls._description.dict()}

    @classmethod
    def _get_status_code(cls):
        return cls._status_code


class BaseInternalException(Exception):
    _description: Optional[str]

    def __init__(self, description=None):
        self._description = description


class RepoBaseException(BaseInternalException):
    pass


class ServiceBaseException(BaseInternalException):
    pass
