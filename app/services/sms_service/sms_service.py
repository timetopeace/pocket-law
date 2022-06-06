import requests
import structlog
from fastapi import Depends

from app.core.enums import Environment
from app.services.sms_service.exceptions import SMSCError
from app.settings import settings
from app.users.repositories.user import UserRepository

logger = structlog.get_logger("sms_service")


class SMSService:

    def __init__(self, user_repository: UserRepository = Depends()):
        self.user_repository = user_repository
        self.test_phones = [f"791000000{str(i).zfill(2)}" for i in range(100)]

    async def send_sms(self, phone: str, code: str) -> None:
        """
        Sends SMS to account's phone, returns status code of response.
        You probably should save code to base and generate message here.
        """
        if phone in self.test_phones:
            code = "0000"
        if phone not in self.test_phones or settings.ENVIRONMENT == Environment.prod:
            self._send_request(phone=phone, code=code)
        await self.user_repository.update_user_code(phone=phone, code=code)

    def _send_request(self, phone: str, code: str):
        try:
            response = requests.get(
                self._generate_request(
                    phone=phone,
                    message=self._generate_message(code=code),
                )
            )
        except Exception as e:
            logger.error(f'{e.args} - SMS was not sent')
            raise ConnectionError('SMSC API request failed')
        if b'ERROR' in response.content:
            logger.error(f'{response.content.decode("utf-8")} - SMS was not sent')
            raise SMSCError()

    @staticmethod
    def _generate_request(phone: str, message: str) -> str:
        return (f"https://smsc.ru/sys/send.php"
                f"?login={settings.SMSC_LOGIN}"
                f"&psw={settings.SMSC_PASS}"
                f"&phones={phone}"
                f"&mes={message}"
                f"&sender={settings.SMSC_SENDER}")

    @staticmethod
    def _generate_message(code: str) -> str:
        """
        Returns generated message.
        """
        return f"Ваш код: {code}\nОт: Pocket Law"
