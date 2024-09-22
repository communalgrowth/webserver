import email
import email.utils
import email.policy
import html.parser


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


def parse_address_from_file(path):
    """Retrieve the sender address from an email stored in a file"""
    with open(path, "rb") as f:
        mail = email.message_from_binary_file(f, policy=email.policy.EmailPolicy())
    return parse_address(mail)


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
        body = plain_body.splitlines()
        try:
            i = body.index("-- ")
            body = body[:i]
        except ValueError:
            pass
        body = [s for s in body if s and not s.isspace()]
    else:
        parser = MyHTMLParser()
        parser.feed(html_body)
        body = parser.data
    return addr, body


def parse_mail_from_file(path):
    """Retrieve the sender address and content body from an email stored in a file

    Returns a pair of the sender address and a list of sentences,
    stripped of HTML if present.
    """
    with open(path, "rb") as f:
        mail = email.message_from_binary_file(f, policy=email.policy.EmailPolicy())
    return parse_mail(mail)
