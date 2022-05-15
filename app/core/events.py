import ssl

import pytest
import structlog
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError

import app.core.database
from app.core.database import get_test_database
from app.core.enums import Collection
from app.settings import settings

logger = structlog.get_logger('events')


async def check_database_connection() -> None:
    """
    Проверяет подключение к базе Mongo на основе данных из клиента app.core.database.mongo_client.
    Происходит попытка подключение к базе, если в течение таймаута база не ответила,
    вызывается исключение ServerSelectionTimeoutError
    Если mongo_client не задан, выбрасывает RuntimeError
    """
    client = app.core.database.mongo_client
    if not isinstance(client, AsyncIOMotorClient):
        raise RuntimeError('Mongo client does not declared')
    logger.info('Connection established on {}:{}'.format(*client.address))


async def startup_event():
    logger.info('Startup')

    if not settings.MONGO_CERT_PATH:
        app.core.database.mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    else:
        app.core.database.mongo_client = AsyncIOMotorClient(
            settings.MONGO_URL,
            ssl_ca_certs=settings.MONGO_CERT_PATH,
            ssl_cert_reqs=ssl.CERT_REQUIRED,
        )

    try:
        await check_database_connection()
    except ServerSelectionTimeoutError as e:
        logger.error(e)
        shutdown_event()
        raise


def shutdown_event():
    logger.info('Shutdown')
    app.core.database.mongo_client.close()


async def startup_test_event():
    logger.info('Startup tests')
    app.core.database.mongo_client = AsyncIOMotorClient(
        settings.TEST_MONGO_URL,
        serverSelectionTimeoutMS=1000,  # 1 second
    )
    try:
        await check_database_connection()
    except ServerSelectionTimeoutError as e:
        pytest.exit(e)
    else:
        logger.info('Clear database')
        db: AsyncIOMotorClient = await get_test_database()

        # Clear data
        for collection in Collection:
            await getattr(db, collection.value).delete_many({})


async def shutdown_test_event():
    logger.info('Shutdown tests')
    app.core.database.mongo_client.close()
