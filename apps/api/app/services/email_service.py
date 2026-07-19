import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:
    def send_verification_code(self, recipient: str, code: str) -> None:
        if not settings.smtp_host:
            if settings.environment == "development" and settings.expose_verification_code:
                return
            raise RuntimeError("邮件服务尚未配置")

        message = EmailMessage()
        message["Subject"] = "Dodomoney 邮箱验证码"
        message["From"] = settings.smtp_from_email
        message["To"] = recipient
        message.set_content(
            f"你的 Dodomoney 验证码是：{code}\n\n"
            f"验证码 {settings.verification_code_ttl_seconds // 60} 分钟内有效，请勿转发给他人。"
        )

        smtp_class = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
        with smtp_class(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
