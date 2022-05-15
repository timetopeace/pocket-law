import smtplib

from app.settings import settings


class MailService:
    _email_from = settings.EMAIL_FROM
    _password = settings.EMAIL_PASSWORD
    _mail_server = settings.EMAIL_SERVER

    def get_message(self, to: str, subject: str, text: str):
        return "\r\n".join((
            f"From: {self._email_from}",
            f"To: {to}",
            f"Subject: {subject}",
            "",
            f"{text}"
        ))

    def send_verification_message(self, to: str, confirm_code: str):
        server = smtplib.SMTP_SSL(self._mail_server)
        server.login(user=self._email_from, password=self._password)
        server.sendmail(
            from_addr=self._email_from,
            to_addrs=to,
            msg=self.get_message(
                to=to,
                subject="Pocket Law Verification",
                # text=f"""
                # Привет!
                # Пройди по ссылке чтобы завершить регистрацию:
                # https://{settings.DOMAIN}/register-confirm/{confirm_code}
                #
                # С наилучшими пожеланиями,
                # Pocket Law
                # """
                text=f"""
                Hi! Follow the link to complete registration: 
                http://{settings.DOMAIN}/user/register-confirm/{confirm_code}/
                
                With best regards,
                Pocket Law
                """
            ),
        )
        server.quit()
