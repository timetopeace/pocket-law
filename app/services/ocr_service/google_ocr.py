import os

import googleapiclient
from fastapi import Depends
from google.oauth2 import service_account

from app.orders.models import Document
from app.orders.repositories.order import OrderRepository
from app.services.ocr_service.base import BaseOCRService
from app.services.s3_service.service import S3Service


class OCRService(BaseOCRService):

    def __init__(
            self,
            order_repository: OrderRepository = Depends(),
            s3_service: S3Service = Depends(),
    ):
        self._order_repository = order_repository
        self._s3_service = s3_service
        self._service = self._get_service()

    def _get_service(self):
        # TODO add key to env and get from settings
        credentials = service_account.Credentials.from_service_account_file(
            os.path.join(
                os.path.dirname(__file__),
                "../PocketLaw/key/ageless-parity-278906-4d13f9f15358.json"
            )
        )
        return googleapiclient.discovery.build('vision', 'v1', credentials=credentials)

    async def _get_image_as_str(self, image_link: str) -> str:
        # TODO complete ocr service
        ...

    async def _get_request_data(self, image_link: str) -> dict:
        return {
            "requests": [{
                "image": {"content": await self._get_image_as_str(image_link=image_link)},
                "features": {"type": "TEXT_DETECTION"},
            }]
        }

    async def get_image_text(self, image_link: str) -> str:
        image_request = await self._get_request_data(image_link=image_link)
        request = self._service.images().annotate(body=image_request)
        response = request.execute()
        return response['responses'][0]['textAnnotations'][0]['description']

    async def apply_ocr(self, order_id: str, document: Document):
        text = ""
        for image in document.input.images:
            text += await self.get_image_text(image_link=image)
        if text:
            await self._order_repository.set_document_text(order_id=order_id, text=text)
