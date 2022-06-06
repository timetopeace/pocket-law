# from unittest.mock import patch
#
# import pytest
#
# from app.services.sms_service.sms_service import SMSService
# from tests.users.conftest import test_faker
#
#
# @pytest.mark.asyncio
# class TestSignup:
#     url = "/user/signup/"
#     fake_email = test_faker.email()
#
#     @pytest.mark.parametrize(
#         "phone",
#         [
#             ("+79129990001"),
#             ("+70000000001"),
#             ("80000000001"),
#             ("+10000000001"),
#             ("9000000001"),
#         ]
#     )
#     async def test_customer(self, client, db_client, mock_sms_client):
#         response = await client.post(
#             "auth/customer",
#             json={
#                 "phone": phone,
#             }
#         )
#         new_user = await db_client.users.find_one({'email.value': self.fake_email})
#         assert new_user is not None
#         assert new_user['md']['referer'] == expected_referer
#         assert response.status_code == 200
#         mock_amo_service.assert_awaited_once()
#         mock_smtp_service.return_value.sendmail.assert_called_once()
#
#     async def test_case_sensitive(self, client, db_client, mock_amo_service, mock_smtp_service):
#         fake_user: dict[str, str] = dict(
#             name=test_faker.name(),
#             email=self.fake_email,
#             password=test_faker.password(),
#             phone=test_faker.phone_number()
#         )
#         await UserRepository(db_client).insert_user(
#             user_data=CreateUserDTO(**fake_user),
#             referer=None
#         )
#
#         fake_user['email'] = fake_user['email'].upper()
#         response = await client.post(
#             self.url,
#             json=fake_user,
#             headers=None
#         )
#         validate_base_exception(UserAlreadyExistsException, response)
#         mock_smtp_service.assert_not_called()
#         mock_smtp_service.return_value.sendmail.assert_not_called()
#