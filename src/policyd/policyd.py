#!/usr/bin/env python3

from time import time
import socketserver as ss
import redis
from app.conf import CG_POLICY_PORT

limit_period = 60 * 60 * 24  # in seconds
email_limit = 100  # per limit period
email_providers = {
    b"aol.com",
    b"bk.ru",
    b"fastmail.com",
    b"fastmail.fm",
    b"gmail.com",
    b"gmx.com",
    b"gmx.de",
    b"gmx.net",
    b"hotmail.com",
    b"icloud.com",
    b"inbox.ru",
    b"keemail.me",
    b"list.ru",
    b"live.com",
    b"mac.com",
    b"mail.ru",
    b"me.com",
    b"messagingengine.com",
    b"msn.com",
    b"outlook.com",
    b"pm.me",
    b"proton.me",
    b"protonmail.com",
    b"rocketmail.com",
    b"tuta.io",
    b"tutamail.com",
    b"tutanota.com",
    b"tutanota.de",
    b"web.de",
    b"ya.ru",
    b"yahoo.com",
    b"yandex.com",
    b"yandex.ru",
    b"ymail.com",
    b"zoho.com",
    b"zohomail.com",
}
accounts_with_quota = {
    b"subscribe@communalgrowth.org",
    b"unsubscribe@communalgrowth.org",
}


def canonicalize_email(email: bytes) -> bytes:
    """Lowercase and remove the +."""
    email = email.lower()
    local, domain = email.split(b"@", 1)
    try:
        local, _ = local.split(b"+", 1)
    except:
        pass
    return b"%b@%b" % (local, domain)


def sender_key(email: bytes) -> bytes:
    """Obtain the Redis key corresponding to email."""
    email = canonicalize_email(email)
    _, domain = email.split(b"@", 1)
    if domain in email_providers:
        key = b"PostfixPolicyQuota-%b" % email
    elif domain.endswith(b".edu"):
        key = b"PostfixPolicyQuota-%b" % email
    else:
        key = b"PostfixPolicyQuota-%b" % domain
    return key


class PostfixPolicy(ss.BaseRequestHandler):
    def handle(self):
        redis_con = redis.Redis(host="localhost", port=6379, protocol=3)
        # We keep a forever loop on the handle.
        #
        # "Unless there was an error, the server must not close the
        # connection, so that the same connection can be used multiple
        # times." See
        # <https://www.postfix.org/SMTPD_POLICY_README.html>.
        while True:
            data = self.request.recv(4096)
            if not data:
                break
            while not data.endswith(b"\n\n"):
                data += self.request.recv(4096)
            lines = data.split()
            d = dict(line.split(b"=", 1) for line in lines)
            self.respond(redis_con, d)

    def respond(self, redis_con, request: dict[bytes, bytes]):
        """Handle and respond to the request"""
        recipient = canonicalize_email(request[b"recipient"])
        if recipient not in accounts_with_quota:
            self.request.send(b"action=DUNNO\n\n")
            return
        key = sender_key(request[b"sender"])
        value = redis_con.get(key)
        if value is None:
            since_time, count = int(time()), 0
        else:
            since_time, count = map(int, value.split(b","))
        count += 1
        cur_time = int(time())
        if cur_time - since_time > limit_period:
            redis_con.set(key, b"%d,%d" % (cur_time, count))
            self.request.send(b"action=DUNNO\n\n")
        elif count > email_limit:
            self.request.send(
                b"action=DEFER_IF_PERMIT 450 4.2.1 Daily quota exceeded.\n\n"
            )
        else:
            redis_con.set(key, b"%d,%d" % (since_time, count))
            self.request.send(b"action=DUNNO\n\n")


def main():
    with ss.TCPServer(("localhost", int(CG_POLICY_PORT)), PostfixPolicy) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
