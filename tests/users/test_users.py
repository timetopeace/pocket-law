import io
from random import randint
from typing import Optional, Dict
from unittest.mock import patch

import pytest
from httpx import Response
from starlette import status

from och.core.database import PydanticObjectId
from och.scoring.utils import timestamp_to_rfc3339
from och.services.amo_service import AmoService
from och.services.mail.scoring_mail_service import ScoringMailService
from och.services.mail_service import MailService
from och.settings import settings
from och.users.exceptions import UnknownOriginException, UserLinkValidationException, UserNotFoundException, \
    UserLinkAlreadyExistsException, UserAlreadyExistsException
from och.users.models import UserModel
from och.users.repositories.user import UserRepository
from och.users.schemas import CreateUserDTO
from tests.e2e.helpers import test_faker
from tests.e2e.tools import validate_base_exception


@pytest.mark.asyncio
class TestUserRecoveryRequest:
    url = "/user/recovery/request/"

    fake_email = test_faker.email()

    @property
    def fake_user(self) -> Dict[str, Optional[CreateUserDTO]]:
        return {
            'user_data': CreateUserDTO(
                name=test_faker.name(),
                email=self.fake_email,
                password=test_faker.password(),
                phone=test_faker.phone_number()
            ),
            'referer': None
        }

    @pytest.mark.parametrize(
        "origin, expected_mail_service",
        [
            (settings.MARKETPLACE_ORIGINS[0], MailService),
            (settings.SCORING_ORIGINS[0], ScoringMailService),
        ],
    )
    @patch("starlette.background.BackgroundTasks.add_task")
    async def test_success(self, add_task, client, db_client, origin, expected_mail_service):
        user_model = await UserRepository(db_client).insert_user(**self.fake_user)

        response = await client.post(self.url, json={"email": self.fake_email}, headers={"origin": origin})
        assert response.status_code == 200

        call_args = add_task.call_args.kwargs
        assert call_args['func'].__self__.__class__ == expected_mail_service
        assert call_args['to'] == self.fake_email

        user_in_db = await db_client.users.find_one({"email.value": self.fake_email})
        assert user_in_db["acl"]["password"] == {
            "recovery": {
                "code": call_args['code']
            },
            "hash": user_model.acl.password.hash
        }

    async def test_wrong_origin(self, client, db_client, mock_send_recovery_message):
        await UserRepository(db_client).insert_user(**self.fake_user)

        response = await client.post(
            url=self.url,
            json={"email": self.fake_email},
            headers={"origin": "unknown_origin"}
        )

        validate_base_exception(UnknownOriginException, response)

    async def test_wrong_email(self, client, db_client, mock_send_recovery_message):
        await UserRepository(db_client).insert_user(**self.fake_user)

        response = await client.post(
            url=self.url,
            json={"email": "wrong_email"},
            headers={"origin": settings.MARKETPLACE_ORIGINS[0]}
        )

        validate_base_exception(UserNotFoundException, response)


@pytest.mark.asyncio
class TestPasswordRecovery:
    url = "/user/recovery/password/"

    async def test_recovery_password(self, client, db_client, not_confirmed_recruiter, create_active_user_in_db):
        recruiter, _ = await create_active_user_in_db(user=not_confirmed_recruiter)
        assert recruiter.email.confirmed is False
        response = await client.post(
            url=self.url,
            json={"email": recruiter.email.value, "code": "recovery_code", "password": "password"},
        )
        assert response.status_code == 200

        recruiter_in_db = await db_client.users.find_one({'email.value': recruiter.email.value})
        assert recruiter_in_db['email']['confirmed'] is True


@pytest.mark.asyncio
class TestGetUserProfile:
    url = "/user/"

    async def test_success(self, client, active_user_without_email_confirmed, create_active_user_in_db):
        active_user, access_token = await create_active_user_in_db(user=active_user_without_email_confirmed)
        response = await client.get(self.url, headers={
            "Authorization": access_token
        })

        assert response.status_code == 200
        assert response.json() == {
            'id': active_user.id,
            'name': active_user.name,
            'email': active_user.email.value,
        }

    async def test_old_style_organisation(
        self, client, active_user_without_email_confirmed, create_active_user_in_db
    ):
        active_user_without_email_confirmed['organisation'] = "test organisation"
        active_user, access_token = await create_active_user_in_db(user=active_user_without_email_confirmed)
        response = await client.get(self.url, headers={
            "Authorization": access_token
        })

        assert response.status_code == 200
        assert response.json() == {
            'id': active_user.id,
            'name': active_user.name,
            'email': active_user.email.value,
            'organisation': {"name": active_user.organisation},
        }


@pytest.mark.asyncio
class TestUpdateUserProfile:
    url = "/user/"

    async def test_update_user_profile_success(
        self, client, db_client, active_user_without_email_confirmed, test_company, create_active_user_in_db
    ):
        user, access_token = await create_active_user_in_db(user=active_user_without_email_confirmed)
        response = await client.post(
            self.url,
            headers={"Authorization": access_token},
            json={
                "name": "new name",
                "shortLink": "new_link",
                "organisation": test_company,
            }
        )
        updated_user = await db_client.users.find_one({"_id": PydanticObjectId(user.id)})
        updated_user_model = UserModel(**updated_user)
        assert response.status_code == 200
        assert response.json() == {
            'id': user.id,
            'name': updated_user_model.name,
            'organisation': updated_user_model.organisation,
            'email': user.email.value,
            'shortLink': updated_user_model.link
        }
        assert updated_user_model.name != user.name
        assert updated_user_model.link != user.link
        assert updated_user_model.organisation != user.organisation
        assert updated_user_model.email == user.email
        assert updated_user_model.phone == user.phone

    @pytest.mark.parametrize(
        "short_link", ["new!link", "new link", "nl"],
    )
    async def test_update_user_profile_validation_fail(
        self, client, db_client, active_user_without_email_confirmed, short_link, create_active_user_in_db
    ):
        user, access_token = await create_active_user_in_db(user=active_user_without_email_confirmed)
        response = await client.post(
            self.url,
            headers={"Authorization": access_token},
            json={
                "name": "new name",
                "shortLink": short_link,
            }
        )
        validate_base_exception(UserLinkValidationException, response)

    async def test_update_user_profile_link_exists_fail(
        self, client, db_client, active_user, active_user_with_link, create_active_user_in_db
    ):
        user_with_link, _ = await create_active_user_in_db(user=active_user_with_link)
        user, token = await create_active_user_in_db(user=active_user)
        response = await client.post(
            self.url,
            headers={"Authorization": token},
            json={
                "name": "new name",
                "shortLink": user_with_link.link,
            }
        )
        validate_base_exception(UserLinkAlreadyExistsException, response)


@pytest.mark.asyncio
class TestSignUp:
    url = "/user/signup/"
    fake_email = test_faker.email()

    @pytest.fixture()
    def mock_amo_service(self):
        with patch.object(AmoService, '_send_request') as mock:
            mock.return_value = Response(
                status_code=status.HTTP_200_OK,
                json={'result': {'contact': randint(100, 1000)}, 'success': True},
            )
            yield mock

    @pytest.mark.parametrize(
        "headers, expected_referer",
        [
            ({"referer": 'test_domain'}, 'test_domain'),
            ({}, None)
        ]
    )
    async def test_success(self, client, db_client, headers, expected_referer, mock_amo_service, mock_smtp_service):
        response = await client.post(
            self.url,
            json={
                "name": test_faker.name(),
                "email": self.fake_email,
                "password": test_faker.password(),
                "phone": test_faker.phone_number()
            },
            headers=headers
        )
        new_user = await db_client.users.find_one({'email.value': self.fake_email})
        assert new_user is not None
        assert new_user['md']['referer'] == expected_referer
        assert response.status_code == 200
        mock_amo_service.assert_awaited_once()
        mock_smtp_service.return_value.sendmail.assert_called_once()

    async def test_case_sensitive(self, client, db_client, mock_amo_service, mock_smtp_service):
        fake_user: dict[str, str] = dict(
            name=test_faker.name(),
            email=self.fake_email,
            password=test_faker.password(),
            phone=test_faker.phone_number()
        )
        await UserRepository(db_client).insert_user(
            user_data=CreateUserDTO(**fake_user),
            referer=None
        )

        fake_user['email'] = fake_user['email'].upper()
        response = await client.post(
            self.url,
            json=fake_user,
            headers=None
        )
        validate_base_exception(UserAlreadyExistsException, response)
        mock_smtp_service.assert_not_called()
        mock_smtp_service.return_value.sendmail.assert_not_called()


@pytest.mark.asyncio
class TestUserCSV:
    url = "/user/csv/"

    @staticmethod
    async def create_user(db_client, with_search_url: bool = True) -> UserModel:
        return await UserRepository(db_client).insert_user(
            CreateUserDTO(
                name=test_faker.name(),
                email=test_faker.email(),
                password=test_faker.password(),
                phone=test_faker.phone_number(),
            ),
            referer=None,
            start_url=test_faker.uri_page() if with_search_url else None,
        )

    async def test_csv(self, client, db_client, mock_send_recovery_message):
        # Создаем пользователей и у последнего не указываем start_url
        users = [await self.create_user(db_client=db_client, with_search_url=bool(i != 2)) for i in range(3)]

        response = await client.get(self.url)
        assert response.status_code == 200

        response_dict = pandas.read_csv(io.BytesIO(response.content), sep=";").to_dict()

        assert response_dict["Name"] == {i: user.name for i, user in enumerate(users)}
        assert response_dict["Phone"] == {i: user.phone for i, user in enumerate(users)}
        assert response_dict["Email"] == {i: user.email.value for i, user in enumerate(users)}
        assert response_dict["Начальная страница"] == {0: users[0].start_url, 1: users[1].start_url, 2: numpy.nan}


@pytest.mark.asyncio
class TestGetUserAnswers:
    url = "/user/answers/"

    async def test_get_answers_by_confirmed_recruiter(
        self, client, active_user, answer_with_question, salary, active_recruiter, create_active_user_in_db,
        create_active_recruiter_in_db, create_answer_in_db
    ):
        active_user_1, _ = await create_active_user_in_db(user=active_user)
        active_user_2, _ = await create_active_user_in_db(
            user={
                'name': 'Mr Test 2',
                'email': {
                    'value': 'mrtest2@test.com',
                    'confirmed': True,
                    'accept': 'cc66a64a-ead7-45dc-bf06-54da9e5a2f48'
                },
                'tokens': [{'value': 'a00c118a-7951-483b-91fa-c942e30738f5'}]
            }
        )
        active_recruiter, token = await create_active_recruiter_in_db(active_recruiter)
        answer_in_db_1 = await create_answer_in_db(
            answer=answer_with_question, uid=active_user_1.id, rid=active_recruiter.id
        )
        answer_in_db_2 = await create_answer_in_db(
            answer=answer_with_question,
            uid=active_user_1.id,
            rid=active_recruiter.id,
            md={
                "ect": answer_in_db_1["md"]["ect"] + 1000,
                "lmt": answer_in_db_1["md"]["lmt"] + 1000,
            },
            salary=salary,
        )
        answer_in_db_3 = await create_answer_in_db(
            answer=answer_with_question,
            uid=active_user_2.id,
            rid=active_recruiter.id,
            md={
                "ect": answer_in_db_1["md"]["ect"] + 2000,
                "lmt": answer_in_db_1["md"]["lmt"] + 2000,
            },
        )
        answer_in_db_4 = await create_answer_in_db(
            answer=answer_with_question,
            uid=active_user_2.id,
            rid=active_recruiter.id,
            md={
                "ect": answer_in_db_1["md"]["ect"] + 3000,
                "lmt": answer_in_db_1["md"]["lmt"] + 3000,
            },
            salary=salary,
        )
        response = await client.get(self.url, headers={"Authorization": token})
        assert response.status_code == 200
        assert response.json() == {
            "talents": [
                {
                    "user": {
                        "id": active_user_2.id,
                        "name": active_user_2.name,
                        "email": active_user_2.email.value,
                    },
                    "offer": {
                        "answers": [
                            {
                                "indexValues": [0],
                                "valueText": "Test",
                                "question": {
                                    "id": answer_in_db_4["answers"][0]["question"]["id"],
                                    "data": {
                                        "en": {
                                            "title": answer_in_db_4["answers"][0]["question"]["data"]["en"]["title"],
                                            "type": answer_in_db_4["answers"][0]["question"]["data"]["en"]["type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                        "ru": {
                                            "title": answer_in_db_4["answers"][0]["question"]["data"]["ru"]["title"],
                                            "type": answer_in_db_4["answers"][0]["question"]["data"]["ru"]["type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                    },
                                    "vacancyData": {
                                        "en": {
                                            "title": answer_in_db_4["answers"][0]["question"]["vacancyData"]["en"][
                                                "title"],
                                            "type": answer_in_db_4["answers"][0]["question"]["vacancyData"]["en"][
                                                "type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                        "ru": {
                                            "title": answer_in_db_4["answers"][0]["question"]["vacancyData"]["ru"][
                                                "title"],
                                            "type": answer_in_db_4["answers"][0]["question"]["vacancyData"]["ru"][
                                                "type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                    },
                                    "key": answer_in_db_4["answers"][0]["question"]["key"],
                                    "position": answer_in_db_4["answers"][0]["question"]["position"],
                                },
                            }
                        ],
                        "md": {"lmt": timestamp_to_rfc3339(answer_in_db_4["md"]["lmt"]),
                               "ect": timestamp_to_rfc3339(answer_in_db_4["md"]["ect"])},
                        "salary": {
                            "min": answer_in_db_4["salary"]["min"],
                            "max": answer_in_db_4["salary"]["max"],
                            "period": answer_in_db_4["salary"]["period"],
                            "currency": answer_in_db_4["salary"]["currency"],
                        },
                    },
                },
                {
                    "user": {
                        "id": active_user_1.id,
                        "name": active_user_1.name,
                        "email": active_user_1.email.value,
                    },
                    "offer": {
                        "answers": [
                            {
                                "indexValues": [0],
                                "valueText": "Test",
                                "question": {
                                    "id": answer_in_db_2["answers"][0]["question"]["id"],
                                    "data": {
                                        "en": {
                                            "title": answer_in_db_2["answers"][0]["question"]["data"]["en"]["title"],
                                            "type": answer_in_db_2["answers"][0]["question"]["data"]["en"]["type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                        "ru": {
                                            "title": answer_in_db_2["answers"][0]["question"]["data"]["ru"]["title"],
                                            "type": answer_in_db_2["answers"][0]["question"]["data"]["ru"]["type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                    },
                                    "vacancyData": {
                                        "en": {
                                            "title": answer_in_db_2["answers"][0]["question"]["vacancyData"]["en"][
                                                "title"],
                                            "type": answer_in_db_2["answers"][0]["question"]["vacancyData"]["en"][
                                                "type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                        "ru": {
                                            "title": answer_in_db_2["answers"][0]["question"]["vacancyData"]["ru"][
                                                "title"],
                                            "type": answer_in_db_2["answers"][0]["question"]["vacancyData"]["ru"][
                                                "type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                    },
                                    "key": answer_in_db_2["answers"][0]["question"]["key"],
                                    "position": answer_in_db_2["answers"][0]["question"]["position"],
                                },
                            }
                        ],
                        "md": {
                            "lmt": timestamp_to_rfc3339(answer_in_db_2["md"]["lmt"]),
                            "ect": timestamp_to_rfc3339(answer_in_db_2["md"]["ect"])
                        },
                        "salary": {
                            "min": answer_in_db_2["salary"]["min"],
                            "max": answer_in_db_2["salary"]["max"],
                            "period": answer_in_db_2["salary"]["period"],
                            "currency": answer_in_db_2["salary"]["currency"],
                        },
                    },
                },
            ]
        }

    async def test_get_answers_by_new_recruiter(
        self, client, active_user, answer_with_question, new_recruiter, create_active_user_in_db,
        create_active_recruiter_in_db, create_answer_in_db,
    ):
        active_user, _ = await create_active_user_in_db(user=active_user)
        active_recruiter, token = await create_active_recruiter_in_db(new_recruiter)
        answer_in_db_1 = await create_answer_in_db(
            answer=answer_with_question, uid=active_user.id, rid=active_recruiter.id
        )
        response = await client.get(self.url, headers={"Authorization": token})
        assert response.status_code == 200
        assert response.json() == {
            "talents": [
                {
                    "user": {
                        "id": active_user.id,
                        "name": active_user.name,
                        "email": active_user.email.value
                    },
                    "offer": {
                        "answers": [
                            {
                                "indexValues": [0],
                                "valueText": "Test",
                                "question": {
                                    "id": answer_in_db_1["answers"][0]["question"]["id"],
                                    "data": {
                                        "en": {
                                            "title": answer_in_db_1["answers"][0]["question"]["data"]["en"]["title"],
                                            "type": answer_in_db_1["answers"][0]["question"]["data"]["en"]["type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                        "ru": {
                                            "title": answer_in_db_1["answers"][0]["question"]["data"]["ru"]["title"],
                                            "type": answer_in_db_1["answers"][0]["question"]["data"]["ru"]["type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                    },
                                    "vacancyData": {
                                        "en": {
                                            "title": answer_in_db_1["answers"][0]["question"]["vacancyData"]["en"][
                                                "title"],
                                            "type": answer_in_db_1["answers"][0]["question"]["vacancyData"]["en"][
                                                "type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                        "ru": {
                                            "title": answer_in_db_1["answers"][0]["question"]["vacancyData"]["ru"][
                                                "title"],
                                            "type": answer_in_db_1["answers"][0]["question"]["vacancyData"]["ru"][
                                                "type"],
                                            "hasOther": False,
                                            "hasRequired": True,
                                            "values": [],
                                        },
                                    },
                                    "key": answer_in_db_1["answers"][0]["question"]["key"],
                                    "position": answer_in_db_1["answers"][0]["question"]["position"],
                                },
                            }
                        ],
                        "md": {
                            "lmt": timestamp_to_rfc3339(answer_in_db_1["md"]["lmt"]),
                            "ect": timestamp_to_rfc3339(answer_in_db_1["md"]["ect"])
                        }
                    },
                }
            ]
        }
