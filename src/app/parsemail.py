# communalgrowth-website, the communalgrowth.org website.
# Copyright (C) 2024  Communal Growth, LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""parsemail.py

Parse an e-mail message to its sender address and document
identifiers.

The main function is :func:`mail_to_docid`.

"""

import email
import email.utils
import email.policy
from email.message import EmailMessage
import html.parser
from itertools import islice
from app import utils
from app import idparser
from app.conf import RATELIMIT_DOCIDS


class MyHTMLParser(html.parser.HTMLParser):
    """Keep the HTML tag content while stripping all tags."""

    def __init__(self):
        super().__init__()
        self.data = []
        self.signature = False

    def handle_data(self, data):
        """Strips email signature"""
        if self.signature:
            return
        if data == "-- ":
            self.signature = True
        elif data and not data.isspace():
            self.data.append(data)


def parse_address(mail: EmailMessage):
    """Retrieve the sender address from an e-mail."""
    _, addr = email.utils.parseaddr(mail["From"])
    return addr


def parse_mail(mail: EmailMessage):
    """Retrieve the sender address and content body from an e-mail.

    Returns a pair of the sender address and a list of sentences,
    stripped of HTML if present.

    """
    # Grab the sender address.
    _, addr = email.utils.parseaddr(mail["From"])
    # Grab the body (stripped of HTML, if present.)
    plain_body = ""
    html_body = ""
    for part in mail.walk():
        charset = part.get_content_charset() or "utf-8"
        match part.get_content_type():
            case "text/plain":
                plain_body += part.get_payload(decode=True).decode(charset)
            case "text/html":
                html_body += part.get_payload(decode=True).decode(charset)
    if plain_body:
        body = utils.splitlines_clean(plain_body)
        try:
            i = body.index("--")
            body = body[:i]
        except ValueError:
            pass
    else:
        parser = MyHTMLParser()
        parser.feed(html_body)
        body = parser.data
    return addr, body


def mail_to_docid(mail: EmailMessage):
    """Retrieve the sender address and document IDs in the body of the e-mail."""
    addr, body = parse_mail(mail)
    # We only split a certain amount of lines; and then we only split
    # a certain amount of comma-separated document IDs from
    # each. Finally, we use islice() to only read a certain amount of
    # items. This prevents users from putting too many \n characters
    # or , characters in their e-mails and slowing down parsing.
    ids = islice(
        (
            idparser.idparse(token)
            for line in body[:RATELIMIT_DOCIDS]
            for token in line.split(",", maxsplit=RATELIMIT_DOCIDS)[:RATELIMIT_DOCIDS]
        ),
        RATELIMIT_DOCIDS,
    )
    ids = [
        (doctype, docid) for (doctype, docid) in ids if doctype != idparser.IDType.TITLE
    ]
    return addr, ids
