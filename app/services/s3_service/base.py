from abc import ABCMeta, abstractmethod

import aiobotocore.session as aio_session
import structlog
from fastapi import UploadFile

logger = structlog.get_logger('s3_service')


class BaseS3(metaclass=ABCMeta):
    def __init__(self):
        self._session = aio_session.get_session()

    @abstractmethod
    def check_file(self, *args, **kwarg) -> None:
        """
        :param args: arguments that are checked
        :param kwarg: arguments that are checked
        :return: None if file is valid or raises Exception
        """
        pass

    @abstractmethod
    def get_key(self, *args, **kwargs) -> str:
        """
        :return: The bucket file key
        """
        pass

    @abstractmethod
    def get_url(self, *args, **kwargs) -> str:
        """
        :return: The url to download file
        """
        pass

    @abstractmethod
    async def upload(self, upload_file: UploadFile, user_id: str, file_size: int) -> str:
        """
        :param upload_file: Thr upload file
        :param user_id: The userID, who uploads file
        :param file_size: The size of uploaded file
        :return: str The file link
        """
        pass
