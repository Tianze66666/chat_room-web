# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from email.message import EmailMessage
from django.conf import settings
import aiosmtplib

async def send_async_email(subject, body, from_email, to_emails):
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    message = EmailMessage()
    message["From"] = from_email
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject
    message.set_content(body)
    smtp = aiosmtplib.SMTP(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        use_tls=False,
        start_tls=False
    )

    await smtp.connect()
    await smtp.starttls()  # 启动 TLS 加密通道
    await smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

    await smtp.send_message(message)
    await smtp.quit()
