import email
import email.utils
import email.policy
import html.parser
from app import utils


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


def parse_address(mail):
    """Retrieve the sender address from an EmailMessage"""
    _, addr = email.utils.parseaddr(mail["From"])
    return addr


def parse_mail(mail):
    """Retrieve the sender address and content body from an EmailMessage

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
