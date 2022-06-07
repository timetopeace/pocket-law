import pytest

from tests.users.conftest import test_faker


@pytest.mark.asyncio
class TestSignin:
    url = "/user/signin/"
    fake_email = test_faker.email()

    @pytest.mark.parametrize(
        "phone",
        [
            ("+79129990001", "0000"),
            ("+70000000001", "1234"),
            ("80000000001", "2134"),
            ("+10000000001", "9420"),
            ("9000000001", "2134"),
        ]
    )
    async def test_customer(self, client, db_client, mock_sms_client, phone, code):
        response = await client.post(
            f"{self.url}customer",
            json={
                "phone": phone,
                "code": code,
            }
        )
        assert response.status_code == 200
        new_user = await db_client.users.find_one({'email.value': self.fake_email})
        assert new_user is not None
        assert new_user['phone'] == phone

    @pytest.mark.parametrize(
        "email, password",
        [
            ("test@mail.ru", "pass"),
            ("someuser@google.com", "D23@(dik&"),
        ]
    )
    async def test_expert(self, client, db_client, mock_smtp_service, email, password):
        response = await client.post(
            f"{self.url}expert",
            json={
                "email": email,
                "password": password,
            }
        )
        assert response.status_code == 200
        new_user = await db_client.users.find_one({'email.value': self.fake_email})
        assert new_user is not None
        assert new_user['email'] == email
