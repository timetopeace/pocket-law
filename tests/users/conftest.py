import faker
import pytest

from tests.users.factories import CustomerFactory, ExpertFactory

test_faker = faker.Faker()


@pytest.fixture()
def customer_factory():
    def _customer_factory(**kwargs):
        return CustomerFactory(**kwargs)
    return _customer_factory


@pytest.fixture()
def expert_factory():
    def _expert_factory(**kwargs):
        return ExpertFactory(**kwargs)
    return _expert_factory
