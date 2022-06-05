from abc import ABCMeta, abstractmethod

from app.orders.models import Document


class BaseOCRService(metaclass=ABCMeta):

    @abstractmethod
    async def get_image_text(self, image_link: str) -> str:
        """

        :param image_link: link to image on file storage
        :return: str text representation of given image
        """
        pass

    @abstractmethod
    async def apply_ocr(self, order_id: str, document: Document):
        """

        :param order_id: str id of order relative to document
        :param document: document object that contained images links
        :return: update order in database and return None
        """
        pass
