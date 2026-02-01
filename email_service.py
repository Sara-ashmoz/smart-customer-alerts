import smtplib
from email.message import EmailMessage


def send_email_smtp(
    host: str,
    port: int,
    user: str,
    password: str,
    to_email: str,
    subject: str,
    body: str,
    from_name: str = "Smart Customer Alerts",
):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{user}>"
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
