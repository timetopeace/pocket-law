from app.core.exception.base import ServiceBaseException


class S3FileSizeIsNotAllowException(ServiceBaseException):
    pass


class S3FileExtensionIsNotAllowException(ServiceBaseException):
    pass


class S3ClientException(ServiceBaseException):
    pass
