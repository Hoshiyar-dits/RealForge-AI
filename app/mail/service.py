import smtplib
from email.message import EmailMessage
from fastapi import HTTPException, status
from app.database.config import smtp_host, smtp_port, smtp_user, smtp_password, smtp_use_tls, mail_from

class MailService():
    def send(self, to: str, subject: str, body: str):
        message = EmailMessage()
        message["From"] = mail_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                if smtp_use_tls:
                    server.starttls()
                if smtp_user:
                    server.login(smtp_user, smtp_password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send email, please try again",
            )
