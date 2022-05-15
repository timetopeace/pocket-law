from typing import Optional

from pydantic import EmailStr, EmailError


def validate_email(email: Optional[str]) -> bool:
    try:
        EmailStr.validate(email)
    except (EmailError, TypeError):
        return False
    else:
        return True
