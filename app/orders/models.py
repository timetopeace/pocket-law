from typing import Optional, List

from pydantic import BaseModel, Field

from app.core.database import PydanticObjectId
from app.orders.enums import OrderStatus, VulnerabilityStatus


class DocumentContent(BaseModel):
    file: Optional[str]
    images: List[str] = []


class Document(BaseModel):
    text: Optional[str]
    input: Optional[DocumentContent]
    result: Optional[DocumentContent]
    vulnerability: VulnerabilityStatus = VulnerabilityStatus.unknown


class Order(BaseModel):
    id: PydanticObjectId = Field(None, alias="_id")
    rating: Optional[float]
    status: OrderStatus = OrderStatus.draft
    customer: str
    expert: Optional[str]
    name: str
    description: Optional[str]
    document: Optional[Document]
