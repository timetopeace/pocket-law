from starlette import status

from app.core.exception.base import AppBaseException, ErrorDescription
from app.core.exception.error_codes import invalid_file_size, invalid_file_extension, s3_client_error, order_not_found, \
    order_wrong_operation_by_status


class FileSizeIsNotAllow(AppBaseException):
    _status_code = status.HTTP_400_BAD_REQUEST
    _code = invalid_file_size
    _description = ErrorDescription(
        en="File size exceeds the maximum limit of 50 mb",
        ru="Размер файла превышает допустимый предел 50 мб",
    )


class FileExtensionIsNotAllow(AppBaseException):
    _status_code = status.HTTP_400_BAD_REQUEST
    _code = invalid_file_extension
    _description = ErrorDescription(
        en="This format is not allowed, upload your file in doc, docx, pdf",
        ru="Недопустимый формат, загрузите файл в doc, docx, pdf",
    )


class ClientFileUploadingError(AppBaseException):
    _status_code = status.HTTP_403_FORBIDDEN
    _code = s3_client_error
    _description = ErrorDescription(
        en="Error external file storage service",
        ru="Ошибка внешнего сервиса хранения файлов",
    )


class OrderNotFound(AppBaseException):
    _status_code = status.HTTP_404_NOT_FOUND
    _code = order_not_found
    _description = ErrorDescription(
        en="Order not found",
        ru="Заказ не найден",
    )


class OrderOperationWrongSatus(AppBaseException):
    _status_code = status.HTTP_400_BAD_REQUEST
    _code = order_wrong_operation_by_status
    _description = ErrorDescription(
        en="This operation prohibited for orders in this status",
        ru="Для заказов в текущем статусе данная операция запрещена",
    )
