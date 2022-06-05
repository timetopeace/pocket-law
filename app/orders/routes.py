from typing import List

from fastapi import APIRouter, Depends, Query, Body, UploadFile, Header, File

from app.orders.enums import OrderStatus, FileType
from app.orders.exceptions import FileExtensionIsNotAllow, FileSizeIsNotAllow, ClientFileUploadingError, OrderNotFound, \
    OrderOperationWrongSatus
from app.orders.repositories.order import OrderRepository
from app.orders.schemas import OrdersResponse, OrderResponse, CreateOrderDTO, FileInfoDTO, RateOrderDTO
from app.orders.serializer import OrderSerializer
from app.services.s3_service.exceptions import S3FileExtensionIsNotAllowException, S3FileSizeIsNotAllowException, \
    S3ClientException
from app.services.s3_service.service import S3Service
from app.users.auth import get_current_user, get_expert, get_customer
from app.users.models import User

order_router = APIRouter(tags=['orders'], prefix="/orders")


@order_router.get(
    path="/",
    response_model=OrdersResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def get_published_orders(
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=1),
        user: User = Depends(get_expert),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    total, orders = await order_repository.get_published_orders(limit=limit, offset=offset)
    return await order_serializer.get_orders_response(
        orders=orders,
        total=total,
        limit=limit,
        offset=offset,
    )


@order_router.get(
    path="/self/",
    response_model=OrdersResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def get_self_orders(
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=1),
        statuses: List[OrderStatus] = Query([]),
        user: User = Depends(get_current_user),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    total, orders = await order_repository.get_self_orders(
        limit=limit,
        offset=offset,
        statuses=statuses,
        user=user,
    )
    return await order_serializer.get_orders_response(
        orders=orders,
        total=total,
        limit=limit,
        offset=offset,
    )


@order_router.post(
    path="/",
    response_model=OrderResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def create_order(
        create_order_request: CreateOrderDTO = Body(),
        user: User = Depends(get_customer),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    order = await order_repository.create_order(order=create_order_request, user=user)
    return await order_serializer.get_order_response(order)


@order_router.post(
    path="/{order_id}/file/input/",
    response_model=OrderResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def upload_file_input(
        order_id: str,
        file_type: FileType = Body(..., alias="fileType"),
        content_length: int = Header(...),
        file: UploadFile = File(),
        user: User = Depends(get_customer),
        s3_service: S3Service = Depends(),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    order = await order_repository.get_order_by_id(order_id=order_id)
    if order.customer != str(user.id):
        raise OrderNotFound()
    try:
        file_link = await s3_service.upload(
            user_id=str(user.id),
            file_size=content_length,
            upload_file=file
        )
        file = FileInfoDTO(
            file_link=file_link,
            file_name=file.filename,
            file_type=file_type,
        )
    except S3FileExtensionIsNotAllowException:
        raise FileExtensionIsNotAllow()
    except S3FileSizeIsNotAllowException:
        raise FileSizeIsNotAllow()
    except S3ClientException:
        raise ClientFileUploadingError()

    order = await order_repository.add_file_to_order_input(order_id=order_id, file=file)
    return await order_serializer.get_order_response(order)


@order_router.post(
    path="/{order_id}/file/result/",
    response_model=OrderResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def upload_file_result(
        order_id: str,
        file_type: FileType = Body(..., alias="fileType"),
        content_length: int = Header(...),
        file: UploadFile = File(),
        user: User = Depends(get_expert),
        s3_service: S3Service = Depends(),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    order = await order_repository.get_order_by_id(order_id=order_id)
    if order.expert != str(user.id):
        raise OrderNotFound()
    try:
        file = FileInfoDTO(
            file_link=await s3_service.upload(
                user_id=str(user.id),
                file_size=content_length,
                upload_file=file
            ),
            file_name=file.filename,
            file_type=file_type,
        )
    except S3FileExtensionIsNotAllowException:
        raise FileExtensionIsNotAllow()
    except S3FileSizeIsNotAllowException:
        raise FileSizeIsNotAllow()
    except S3ClientException:
        raise ClientFileUploadingError()

    order = await order_repository.add_file_to_order_result(order_id=order_id, file=file)
    return await order_serializer.get_order_response(order)


@order_router.post(
    path="/{order_id}/cancel/",
    response_model=OrderResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def cancel_order(
        order_id: str,
        user: User = Depends(get_current_user),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    order = await order_repository.get_order_by_id(order_id=order_id)
    if not order or order.customer != str(user.id) and order.expert != str(user.id):
        raise OrderNotFound()
    if any([
        order.customer == str(user.id) and order.status not in [OrderStatus.draft, OrderStatus.published],
        order.expert == str(user.id) and order.status != OrderStatus.handling,
    ]):
        raise OrderOperationWrongSatus()
    order = await order_repository.change_oder_status(order_id=order_id, status=OrderStatus.cancelled)
    # TODO send push notification to customer
    return await order_serializer.get_order_response(order)


@order_router.post(
    path="/{order_id}/confirm/",
    response_model=OrderResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def confirm_order(
        order_id: str,
        user: User = Depends(get_customer),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    order = await order_repository.get_order_by_id(order_id=order_id)
    if not order or order.customer != str(user.id):
        raise OrderNotFound()
    if order.status != OrderStatus.draft.value:
        raise OrderOperationWrongSatus()
    order = await order_repository.change_oder_status(order_id=order_id, status=OrderStatus.published)
    # TODO add OCR load pictures
    return await order_serializer.get_order_response(order)


@order_router.post(
    path="/{order_id}/rate/",
    response_model=OrderResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def rate_order(
        order_id: str,
        rate_request: RateOrderDTO,
        user: User = Depends(get_customer),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    order = await order_repository.get_order_by_id(order_id=order_id)
    if not order or order.customer != str(user.id):
        raise OrderNotFound()
    if order.status != OrderStatus.draft.value:
        raise OrderOperationWrongSatus()
    order = await order_repository.set_rating(order_id=order_id, rating=rate_request.rating)
    # TODO update expert rating
    return await order_serializer.get_order_response(order)


@order_router.post(
    path="/{order_id}/accept/",
    response_model=OrderResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def accept_order(
        order_id: str,
        user: User = Depends(get_expert),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    order = await order_repository.get_order_by_id(order_id=order_id)
    if not order or order.expert:
        raise OrderNotFound()
    if order.status != OrderStatus.published.value:
        raise OrderOperationWrongSatus()
    order = await order_repository.set_expert(order_id=order_id, expert_id=str(user.id))
    # TODO send push notification to customer
    return await order_serializer.get_order_response(order)


@order_router.post(
    path="/{order_id}/complete/",
    response_model=OrderResponse,
    response_model_exclude_none=True,
    response_model_by_alias=True,
)
async def complete_order(
        order_id: str,
        user: User = Depends(get_expert),
        order_repository: OrderRepository = Depends(),
        order_serializer: OrderSerializer = Depends(),
):
    order = await order_repository.get_order_by_id(order_id=order_id)
    if not order or order.customer != str(user.id):
        raise OrderNotFound()
    if order.status != OrderStatus.handling.value:
        raise OrderOperationWrongSatus()
    # TODO check and set vulnerability
    order = await order_repository.change_oder_status(order_id=order_id, status=OrderStatus.done)
    # TODO send push notification to customer
    return await order_serializer.get_order_response(order)
