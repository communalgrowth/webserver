from __future__ import annotations

import pytest

from app import parsemail
from email.message import EmailMessage


@pytest.fixture(
    params=[
        "user@example.invalid",
        "<user@example.invalid>",
        "Some User <user@example.invalid>",
        "Some User<user@example.invalid>",
    ]
)
def sender_address(request):
    return request.param


@pytest.fixture(
    params=[
        ("Hello there!\nHow are you?\n", ["Hello there!", "How are you?"]),
        ("Communal Growth!", ["Communal Growth!"]),
    ]
)
def mail_body(request):
    return request.param[0], request.param[1]


@pytest.fixture(
    params=[
        (
            "<p><b>Hello</b> there!\nHow are you?\n</p>",
            ["Hello", " there!\nHow are you?\n"],
        ),
        (
            '<a href="https://communalgrowth.org">Communal Growth!</a>',
            ["Communal Growth!"],
        ),
    ]
)
def mail_html_body(request):
    return request.param[0], request.param[1]


@pytest.fixture
def mail(sender_address, mail_body):
    message = EmailMessage()
    message["From"] = sender_address
    message["To"] = "subscribe@communalgrowth.org"
    message["Subject"] = "Long time no see"
    message.set_content(mail_body[0])
    return message, mail_body[1]


@pytest.fixture
def mail_html(sender_address, mail_html_body):
    message = EmailMessage()
    message["From"] = sender_address
    message["To"] = "subscribe@communalgrowth.org"
    message["Subject"] = "Long time no see"
    message.set_content(mail_html_body[0], subtype="html")
    return message, mail_html_body[1]


@pytest.fixture
def sender_address_actual():
    return "user@example.invalid"


def test_parse_address(mail, sender_address_actual):
    message, _ = mail
    sender_addr = parsemail.parse_address(message)
    assert sender_addr == sender_address_actual


def test_parse_mail(mail, sender_address_actual):
    message, body_actual = mail
    sender_address, body = parsemail.parse_mail(message)
    assert sender_address == sender_address_actual
    assert body == body_actual


def test_parse_mail_html(mail_html, sender_address_actual):
    message, body_actual = mail_html
    sender_address, body = parsemail.parse_mail(message)
    assert sender_address == sender_address_actual
    assert body == body_actual
