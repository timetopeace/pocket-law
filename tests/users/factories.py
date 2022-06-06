import random

import factory
import faker

from app.core.database import PydanticObjectId
from app.users.enums import UserRole
from app.users.models import User, PasswordRecovery, ACLPassword, UserACL, UserToken


class PasswordRecoveryFactory(factory.Factory):
    code = 'some_code'

    class Meta:
        model = PasswordRecovery


class ACLPasswordFactory(factory.Factory):
    hash = 'some_hash'
    recovery: factory.SubFactory(PasswordRecoveryFactory)

    class Meta:
        model = ACLPassword


class UserACLFactory(factory.Factory):
    password = factory.SubFactory(ACLPasswordFactory)
    code = "".join([str(random.randint(0, 9)) for _ in range(4)])

    class Meta:
        model = UserACL


class UserTokenFactory(factory.Factory):
    value = factory.Faker('uuid4')

    class Meta:
        model = UserToken


class UserMDFactory(factory.Factory):
    lmt = 1640995200
    ect = 1640995200
    role = UserRole.expert


class UserFactory(factory.Factory):
    id = PydanticObjectId()
    name = faker.Faker("name")
    acl = factory.SubFactory(UserACLFactory)
    tokens = factory.List([factory.SubFactory(UserTokenFactory) for _ in range(1)])
    rating = random.uniform(3, 5)


class CustomerFactory(UserFactory):
    phone = faker.Faker("phone")
    md = factory.SubFactory(UserMDFactory, role=UserRole.customer)

    class Meta:
        model = User


class ExpertFactory(UserFactory):
    email = faker.Faker("email")
    md = factory.SubFactory(UserMDFactory, role=UserRole.expert)

    class Meta:
        model = User
