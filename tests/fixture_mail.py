from __future__ import annotations
from email.message import EmailMessage
import pytest


@pytest.fixture(
    params=[
        ("user@example.invalid", "user@example.invalid"),
        ("<user@example.invalid>", "user@example.invalid"),
        ("Some User <user@example.invalid>", "user@example.invalid"),
        ("Some User<user@example.invalid>", "user@example.invalid"),
    ]
)
def sender_address(request):
    return request.param


@pytest.fixture(
    params=[
        (
            "0140328726\n10.1038/248030a0, 1708.05919\n",
            ["0140328726", "10.1038/248030a0, 1708.05919"],
        ),
        (
            "0140328726,10.1038/248030a0, 1708.05919\n",
            ["0140328726,10.1038/248030a0, 1708.05919"],
        ),
        (
            "0140328726\n10.1038/248030a0\n1708.05919\n",
            ["0140328726", "10.1038/248030a0", "1708.05919"],
        ),
    ]
)
def mail_text_body(request):
    return request.param


@pytest.fixture(
    params=[
        (
            "<p><ul><li>0140328726</li><li>10.1038/248030a0, 1708.05919</li></ul></p>",
            ["0140328726", "10.1038/248030a0, 1708.05919"],
        ),
        (
            "<p><ul><li>0140328726,10.1038/248030a0, 1708.05919</li></ul></p>",
            ["0140328726,10.1038/248030a0, 1708.05919"],
        ),
        (
            "<p><ul><li>0140328726</li><li>10.1038/248030a0</li><li>1708.05919</li></ul></p>",
            ["0140328726", "10.1038/248030a0", "1708.05919"],
        ),
    ]
)
def mail_html_body(request):
    return request.param


@pytest.fixture(
    params=[
        (
            "0140328726\n10.1038/248030a0, 1708.05919\n",
            "<p><ul><li>0140328726</li><li>10.1038/248030a0, 1708.05919</li></ul></p>",
            ["0140328726", "10.1038/248030a0, 1708.05919"],
        ),
        (
            "0140328726,10.1038/248030a0, 1708.05919\n",
            "<p><ul><li>0140328726,10.1038/248030a0, 1708.05919</li></ul></p>",
            ["0140328726,10.1038/248030a0, 1708.05919"],
        ),
        (
            "0140328726\n10.1038/248030a0\n1708.05919\n",
            "<p><ul><li>0140328726</li><li>10.1038/248030a0</li><li>1708.05919</li></ul></p>",
            ["0140328726", "10.1038/248030a0", "1708.05919"],
        ),
    ]
)
def mail_alt_body(request):
    return request.param


@pytest.fixture
def mail_text(mail_text_body, sender_address):
    body, actual_body = mail_text_body
    addr, actual_addr = sender_address
    message = EmailMessage()
    message["From"] = addr
    message["To"] = "subscribe@communalgrowth.org"
    message["Subject"] = "Long time no see"
    message.set_content(body)
    return message, dict(addr=actual_addr, body=actual_body)


@pytest.fixture
def mail_html(mail_html_body, sender_address):
    body, actual_body = mail_html_body
    addr, actual_addr = sender_address
    message = EmailMessage()
    message["From"] = addr
    message["To"] = "subscribe@communalgrowth.org"
    message["Subject"] = "Long time no see"
    message.set_content(body, subtype="html")
    return message, dict(addr=actual_addr, body=actual_body)


@pytest.fixture
def mail_alt(mail_alt_body, sender_address):
    body_text, body_html, actual_body = mail_alt_body
    addr, actual_addr = sender_address
    message = EmailMessage()
    message["From"] = addr
    message["To"] = "subscribe@communalgrowth.org"
    message["Subject"] = "Long time no see"
    message.set_content(body_html, subtype="html")
    message.add_alternative(body_text, subtype="text")
    return message, dict(addr=actual_addr, body=actual_body)
