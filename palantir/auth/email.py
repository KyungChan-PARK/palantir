import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from .config import settings

class EmailManager:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "")

    def send_reset_password_email(self, to_email: str, reset_token: str) -> bool:
        """
        비밀번호 재설정 이메일 발송
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = "비밀번호 재설정 요청"

            reset_url = f"http://localhost:8501/reset-password?token={reset_token}"
            body = f"""
            안녕하세요,

            비밀번호 재설정을 요청하셨습니다.
            아래 링크를 클릭하여 비밀번호를 재설정해주세요:

            {reset_url}

            이 링크는 1시간 동안만 유효합니다.
            본인이 요청하지 않은 경우 이 이메일을 무시해주세요.

            감사합니다.
            """

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"이메일 발송 실패: {str(e)}")
            return False

    def send_verification_email(self, to_email: str, verify_token: str) -> bool:
        """
        이메일 인증 링크 발송
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = "이메일 주소 인증"

            verify_url = f"http://localhost:8501/verify-email?token={verify_token}"
            body = f"""
            안녕하세요,

            이메일 주소 인증을 위해 아래 링크를 클릭해주세요:

            {verify_url}

            이 링크는 24시간 동안만 유효합니다.

            감사합니다.
            """

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"이메일 발송 실패: {str(e)}")
            return False

email_manager = EmailManager() 