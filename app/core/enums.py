from enum import Enum, unique


class Environment(str, Enum):
    dev = "DEV"
    stage = "STAGE"
    prod = "PROD"


@unique
class Collection(str, Enum):
    USERS = "users"
    ORDERS = "orders"
