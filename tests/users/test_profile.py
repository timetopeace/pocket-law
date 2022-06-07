import pytest


@pytest.mark.asyncio
class TestGetProfile:
    url = "/user/"

    async def test_customer(self, client, db_client, customer_factory, create_user_in_db):
        user = customer_factory()
        user, token = create_user_in_db(user)
        response = await client.get(
            self.url,
            headers={"Authorization": token}
        )
        assert response.status_code == 200
        assert response["email"] == user.email.value

    async def test_expert(self, client, db_client, expert_factory, create_user_in_db):
        user = expert_factory()
        user, token = create_user_in_db(user)
        response = await client.get(
            self.url,
            headers={"Authorization": token}
        )
        assert response.status_code == 200
        assert response["email"] == user.email.value


@pytest.mark.asyncio
class TestUpdateProfile:
    url = "/user/"

    async def test_expert(self, client, db_client, expert_factory, create_user_in_db):
        user = expert_factory()
        user, token = create_user_in_db(user)
        response = await client.patch(
            self.url,
            json={
                "name": "new name"
            },
            headers={"Authorization": token}
        )
        assert response.status_code == 200
        assert response["name"] == "new name"
