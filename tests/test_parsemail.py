from __future__ import annotations

import pytest

from app import parsemail

from fixture_mail import *


def test_parse_address(mail_text):
    message, actual = mail_text
    sender_addr = parsemail.parse_address(message)
    assert sender_addr == actual["addr"]


def test_parse_mail(mail_text):
    message, actual = mail_text
    sender_address, body = parsemail.parse_mail(message)
    assert sender_address == actual["addr"]
    assert body == actual["body"]


def test_parse_mail_html(mail_html):
    message, actual = mail_html
    sender_address, body = parsemail.parse_mail(message)
    assert sender_address == actual["addr"]
    assert body == actual["body"]


def test_parse_mail_alt(mail_alt):
    """Test HTML e-mail with alternative text

    Text is always prioritized over HTML, so HTML gets ignored in this
    instance."""
    message, actual = mail_alt
    sender_address, body = parsemail.parse_mail(message)
    assert sender_address == actual["addr"]
    assert body == actual["body"]
