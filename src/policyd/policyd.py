#!/usr/bin/env python3

import socketserver as ss
import redis


class PostfixPolicy(ss.BaseRequestHandler):
    def __init__(self):
        self.redis_con = redis.Redis(host="localhost", port=6379, protocol=3)

    def handle(self):
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
            self.respond(d)

    def respond(self, request: dict[bytes, bytes]):
        """Handle and respond to the request"""
        email = request[b"sender"]
        username, domain = email.split(b"@", 1)
        key = b"PostfixPolicyQuota-%b" % email
        count = self.redis_con.get(key)
        if count > 100:
            self.request.send(
                b"action=DEFER_IF_PERMIT 450 4.2.1 Daily quota exceeded.\n\n"
            )
        else:
            self.request.send(b"action=OK\n\n")


def main():
    with ss.TCPServer(("localhost", 12345), PostfixPolicy) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
