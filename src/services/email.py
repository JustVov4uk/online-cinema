def send_activation_email(email: str, token: str) -> None:
    activation_link = f"http://localhost:8000/api/v1/auth/activate?token={token}"

    print(f"Activation email to {email}: {activation_link}")


def send_password_reset_email(email: str, token: str) -> None:
    password_reset_link = (
        f"http://localhost:8000/api/v1/auth/password-reset/confirm?token={token}"
    )

    print(f"Password reset email to {email}: {password_reset_link}")
