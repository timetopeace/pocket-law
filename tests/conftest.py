from typing import Tuple
from unittest import mock
from unittest.mock import AsyncMock

import pytest
from asgi_lifespan import LifespanManager
from fastapi_jwt_auth import AuthJWT
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.app import create_app
from app.core.database import get_test_database
from app.settings import settings
from app.users.models import User

app = create_app(testing=True)


# @pytest.fixture
# def override_settings():
#     yield tests.helpers.override_settings


@pytest.fixture()
async def client():
    async with AsyncClient(app=app, base_url=f'http://{settings.DOMAIN_SCORING}') as client, LifespanManager(app):
        yield client


@pytest.fixture()
async def db_client(client):
    db: AsyncIOMotorClient = await get_test_database()
    yield db


@pytest.fixture()
def create_user_in_db(db_client):
    async def _create_user_in_db(user) -> Tuple[User, str]:
        user = await db_client.users.insert_one(user)
        user_in_db = await db_client.users.find_one({"_id": user.inserted_id})
        access_token = AuthJWT().create_access_token(subject=user_in_db['email']['value'])

        return User(**user_in_db), f'Bearer {access_token}'

    return _create_user_in_db


@pytest.fixture()
def mock_sms_client():
    with mock.patch(
            "app.services.sms_service.SMSService.send_sms",
            autospec=True
    ) as mocked_method:
        yield mocked_method
