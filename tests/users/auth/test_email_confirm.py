import pytest

from tests.users.conftest import test_faker


@pytest.mark.asyncio
class TestEmailConfirm:
    url = "/user/register-confirm/"
    fake_email = test_faker.email()

    async def test_customer(self, client, db_client, user_factory):
        user = user_factory()
        response = await client.get(f"{self.url}{user.email.accept}")
        assert response.status_code == 200
        db_user = await db_client.users.find_one({'email.value': user.email.value})
        assert db_user["email"]["confirmed"] == True
