import pytest

from tests.users.conftest import test_faker


@pytest.mark.asyncio
class TestSignup:
    url = "/user/signup/"
    fake_email = test_faker.email()

    @pytest.mark.parametrize(
        "phone",
        [
            ("+79129990001"),
            ("+70000000001"),
            ("80000000001"),
            ("+10000000001"),
            ("9000000001"),
        ]
    )
    async def test_customer(self, client, db_client, mock_sms_client, phone):
        response = await client.post(
            "user/auth/customer",
            json={
                "phone": phone,
            }
        )
        assert response.status_code == 200
        new_user = await db_client.users.find_one({'email.value': self.fake_email})
        assert new_user is not None
        assert new_user['phone'] == phone

    @pytest.mark.parametrize(
        "name, email, password",
        [
            ("testuser", "test@mail.ru", "pass"),
            ("someuser", "someuser@google.com", "D23@(dik&"),
        ]
    )
    async def test_expert(self, client, db_client, mock_smtp_service, name, email, password):
        response = await client.post(
            "user/singup/expert",
            json={
                "name": name,
                "email": email,
                "password": password,
            }
        )
        assert response.status_code == 200
        new_user = await db_client.users.find_one({'email.value': self.fake_email})
        assert new_user is not None
        assert new_user['email'] == email
