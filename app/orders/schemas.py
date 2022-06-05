from typing import Optional, List, Type

from pydantic import BaseModel

from app.orders.enums import OrderStatus, VulnerabilityStatus, FileType
from app.orders.models import Document, DocumentContent
from app.users.schemas import UserFullResponse


class DocumentContentResponse(BaseModel):
    file: Optional[str]
    images: List[str] = []

    @classmethod
    def from_model(cls: Type[BaseModel], content: DocumentContent):
        return cls(
            file=content.file,
            images=content.images,
        )


class DocumentResponse(BaseModel):
    input: Optional[DocumentContentResponse]
    result: Optional[DocumentContentResponse]
    vulnerability: VulnerabilityStatus

    @classmethod
    def from_model(cls: Type[BaseModel], document: Document):
        return cls(
            input=DocumentContentResponse.from_model(document.input) if document.input else None,
            result=DocumentContentResponse.from_model(document.result) if document.result else None,
            vulnerability=document.vulnerability,
        )


class OrderResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: OrderStatus
    rating: float
    customer: UserFullResponse
    expert: Optional[UserFullResponse]
    document: Optional[DocumentResponse]


class Pagination(BaseModel):
    limit: Optional[int] = None
    offset: Optional[int] = None
    total: int


class OrdersResponse(BaseModel):
    items: List[OrderResponse]
    pagination: Pagination


class FileInfoDTO(BaseModel):
    file_link: str
    file_name: str
    file_type: FileType


class CreateOrderDTO(BaseModel):
    name: str
    description: Optional[str]


class RateOrderDTO(BaseModel):
    rating: float
