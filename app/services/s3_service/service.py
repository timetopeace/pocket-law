import mimetypes

import structlog
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.services.s3_service.base import BaseS3
from app.services.s3_service.exceptions import S3FileExtensionIsNotAllowException, S3FileSizeIsNotAllowException, \
    S3ClientException
from app.settings import settings

logger = structlog.get_logger('s3_service')


class S3Service(BaseS3):
    def __init__(self, ):
        super().__init__()

    def check_file(self, ext: str, file_size: int) -> None:
        if ext not in settings.ALLOW_FILE_EXTENSION:
            logger.debug(f'File extension {ext} not allowed')
            raise S3FileExtensionIsNotAllowException()
        elif file_size > settings.MAX_FILE_SIZE:
            logger.debug(f'File size {file_size} not allowed')
            raise S3FileSizeIsNotAllowException()

    def get_key(self, user_id: str, ext: str) -> str:
        return f'{user_id}{ext}'

    def get_url(self, domain: str, key: str) -> str:
        return f'{domain}/{settings.S3_BUCKET}/{key}'

    def guess_extension(self, upload_file: UploadFile) -> str:
        if ext_by_content_type := mimetypes.guess_extension(upload_file.content_type):
            logger.debug(f'Extension guessed by Content-Type: {upload_file.content_type} -> {ext_by_content_type}')
            return ext_by_content_type
        logger.debug(f'Could not guess extension by Content-Type: {upload_file.content_type}')
        ext_by_filename = upload_file.filename.split('.')[-1]
        return f'.{ext_by_filename}'

    async def upload(self, upload_file: UploadFile, user_id: str, file_size: int) -> str:
        ext: str = self.guess_extension(upload_file)

        self.check_file(ext, file_size)

        key: str = self.get_key(user_id, ext)

        logger.debug(f'Uploading cv file: Start! UserId: {user_id}')

        return await self._upload(
            upload_file=upload_file,
            key=key,
            user_id=user_id
        )

    async def _upload(self, upload_file: UploadFile, key: str, user_id: str) -> str:
        try:
            async with self._session.create_client(
                    's3',
                    region_name=settings.S3_REGION,
                    endpoint_url=settings.S3_ENDPOINT,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY
            ) as s3_client:
                await s3_client.put_object(
                    ACL='public-read',
                    Bucket=settings.S3_BUCKET,
                    Key=key,
                    Body=upload_file.file._file,
                    ContentType=upload_file.content_type,
                )
        except ClientError as e:
            logger.error(f"Uploading file finished with error: {e.response.get('Error')}")
            raise S3ClientException()

        logger.debug(f'Uploading file: Success! UserId: {user_id}')

        return self.get_url(domain=settings.S3_ENDPOINT, key=key)
