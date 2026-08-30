from src.core.celery_app import celery_app
from src.services.email import send_activation_email, send_password_reset_email


@celery_app.task(name="emails.send_activation_email")
def send_activation_email_task(email: str, token: str) -> None:
    send_activation_email(email=email, token=token)


@celery_app.task(name="emails.send_password_reset_email")
def send_password_reset_email_task(email: str, token: str) -> None:
    send_password_reset_email(email=email, token=token)
