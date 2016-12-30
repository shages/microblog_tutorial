"""MOdule to handle emails such as notifications."""

from flask import render_template
from flask_mail import Message
from app import app, mail
from config import ADMINS
from .decorators import threadasync


@threadasync
def send_async_email(app, msg):
    """Send email with app context in a separate thread."""
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    """Send an email through our mail server."""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(app, msg)


def follower_notification(followed, follower):
    """Send users a notification that someone is following them."""
    send_email(
        '[microblog] {0} is now following you!'.format(follower.nickname),
        ADMINS[0],
        [followed.email],
        render_template('follower_email.txt',
                        user=followed,
                        follower=follower),
        render_template('follower_email.html',
                        user=followed,
                        follower=follower))
