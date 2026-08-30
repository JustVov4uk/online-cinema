import smtplib
from email.message import EmailMessage

from src.core.config import get_settings


def send_email(to_email: str, subject: str, body: str) -> None:
    settings = get_settings()

    if not settings.EMAIL_ENABLED:
        return

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body, cte="8bit")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.send_message(message)


def send_activation_email(email: str, token: str) -> None:
    settings = get_settings()
    activation_link = f"{settings.FRONTEND_BASE_URL}/api/v1/auth/activate?token={token}"
    body = (
        "Welcome to Online Cinema.\n\n"
        "Use this token to activate your account:\n"
        f"{token}\n\n"
        "Activation link:\n"
        f"{activation_link}\n"
    )

    send_email(
        to_email=email,
        subject="Activate your Online Cinema account",
        body=body,
    )


def send_password_reset_email(email: str, token: str) -> None:
    settings = get_settings()
    password_reset_link = (
        f"{settings.FRONTEND_BASE_URL}/api/v1/auth/password-reset/confirm?token={token}"
    )
    body = (
        "You requested a password reset for Online Cinema.\n\n"
        "Use this token to reset your password:\n"
        f"{token}\n\n"
        "Password reset link:\n"
        f"{password_reset_link}\n"
    )

    send_email(
        to_email=email,
        subject="Reset your Online Cinema password",
        body=body,
    )
