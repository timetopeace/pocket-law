from app.core.exception.base import RepoBaseException


class UserInDBAlreadyExistsException(RepoBaseException):
    pass


class UserInDBNotFoundException(RepoBaseException):
    pass
