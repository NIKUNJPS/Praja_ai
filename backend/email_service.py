import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Send an email using the SMTP settings from config.
    Raises an exception if sending fails.
    """
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        # Re-raise the exception so the caller can handle it (e.g., background task failure)
        raise

def send_otp_email(to_email: str, otp: str, purpose: str) -> None:
    """
    Send an OTP email for a given purpose (registration or password reset).
    """
    if purpose == "registration":
        subject = "Verify your email - ICIOS"
        body = (
            f"Your OTP for email verification is: {otp}\n"
            f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
            "If you did not request this, please ignore this email."
        )
    elif purpose == "password_reset":
        subject = "Password Reset OTP - ICIOS"
        body = (
            f"Your OTP for password reset is: {otp}\n"
            f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
            "If you did not request a password reset, please ignore this email."
        )
    else:
        subject = "Your OTP - ICIOS"
        body = f"Your OTP is: {otp}"

    send_email(to_email, subject, body)

def send_welcome_email(to_email: str, name: str) -> None:
    """
    Send a welcome email after successful email verification.
    """
    subject = "Welcome to ICIOS"
    body = (
        f"Hello {name},\n\n"
        "Your account has been successfully verified. "
        "Welcome to the India Civic Intelligence OS!\n\n"
        "You can now log in and start exploring the platform.\n\n"
        "Thank you,\n"
        "The ICIOS Team"
    )
    send_email(to_email, subject, body)

def send_password_reset_confirmation(to_email: str) -> None:
    """
    Send a confirmation email after a successful password reset.
    """
    subject = "Password Changed - ICIOS"
    body = (
        "Your password has been successfully changed.\n\n"
        "If you did not request this change, please contact support immediately.\n\n"
        "Thank you,\n"
        "The ICIOS Team"
    )
    send_email(to_email, subject, body)