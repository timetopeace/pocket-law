from enum import Enum


class UserRole(str, Enum):
    customer = "customer"
    expert = "expert"
