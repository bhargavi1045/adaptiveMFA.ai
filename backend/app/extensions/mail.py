from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from app.config import settings

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=587, 
    MAIL_SERVER="smtp.gmail.com",  
    MAIL_STARTTLS=True,   
    MAIL_SSL_TLS=False,   
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fast_mail = FastMail(mail_config)

async def send_email(to_email: str, subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=body,
        subtype="html"
    )
    fm = FastMail(mail_config)
    await fm.send_message(message)