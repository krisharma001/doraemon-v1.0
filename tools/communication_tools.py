import logging
import os
import smtplib
import pywhatkit
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from livekit.agents import function_tool, RunContext
from twilio.rest import Client

@function_tool()
async def send_whatsapp_message(
    context: RunContext, # type: ignore
    phone: str,
    message: str
) -> str:
    """
    Send a WhatsApp message using pywhatkit.
    Phone number should be in international format (e.g., '+919876543210').
    """
    try:
        logging.info(f"Sending WhatsApp message to {phone}")
        # pywhatkit.sendwhatmsg_instantly is synchronous
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: pywhatkit.sendwhatmsg_instantly(phone, message))
        return f"WhatsApp message sent to {phone}, Sir."
    except Exception as e:
        logging.error(f"WhatsApp failed: {e}")
        return f"Failed to send WhatsApp message: {str(e)}"

@function_tool()
async def send_sms(
    context: RunContext, # type: ignore
    phone: str,
    message: str
) -> str:
    """
    Send an SMS using Twilio.
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER")

        if not all([account_sid, auth_token, from_number]):
            return "SMS failed: Twilio credentials not configured, Sir."

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=phone
        )
        return f"SMS sent successfully to {phone}, Sir."
    except Exception as e:
        logging.error(f"SMS failed: {e}")
        return f"Failed to send SMS: {str(e)}"

@function_tool()
async def send_email(
    context: RunContext, # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None,
    is_html: bool = False
) -> str:
    """
    Send an email through Gmail with support for HTML.
    """
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_password:
            return "Email sending failed: Gmail credentials not configured."

        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject

        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)

        # Attach body as plain text or HTML
        mime_type = 'html' if is_html else 'plain'
        msg.attach(MIMEText(message, mime_type))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
        server.quit()

        return f"Email sent successfully to {to_email}, Sir."
    except Exception as e:
        logging.error(f"Email failed: {e}")
        return f"An error occurred while sending email: {str(e)}"
