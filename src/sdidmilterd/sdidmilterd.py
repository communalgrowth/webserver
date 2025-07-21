#!/usr/bin/env python3

# sdidmilterd, Milter daemon for RFC5322.From and DKIM SDID alignment.
# Copyright (C) 2025  Communal Growth, LLC
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

import Milter
import re
from email.utils import parseaddr
from app.conf import CG_SDIDMILTER_PORT

smtp_multiline_regex = re.compile(r"\r\n\s+")


def parse_dkim_signature(s):
    """Convert the DKIM-Signature: header tags into a dictionary."""
    s = s.removeprefix("DKIM-Signature:")
    unfold_multilines = smtp_multiline_regex.sub("", s)
    fields = unfold_multilines.split(";")
    d = {}
    for field in fields:
        k, v = field.split("=", 1)
        d[k.strip()] = v.strip()
    return d


class CompareRFC5322FromToDKIMSDID(Milter.Base):
    def __init__(self):
        self.sdid = None
        self.domain = None
        self.signedfrom = False
        self.exception_occurred = False

    @Milter.noreply
    def envfrom(self, mailfrom, *str):
        del str
        _, addr = parseaddr(mailfrom)
        try:
            self.domain = addr.split("@", 1)[1].lower()
        except:
            self.exception_occurred = True
        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name, hval):
        s = name.lower()
        if s == "from":
            try:
                _, addr = parseaddr(hval)
                self.rfc5322from = addr
            except:
                self.exception_occurred = True
        elif self.sdid is None and s == "dkim-signature":
            # Note that if self.sdid is not None, then we have already
            # encountered a DKIM-Signature. Thus this function
            # considers only the first DKIM-Signature with d= and h=
            # encountered.
            try:
                dkim = parse_dkim_signature(hval)
                if "d" in dkim and "h" in dkim:
                    self.signedfrom = "from" in dkim["h"].lower().split(":")
                    self.sdid = dkim["d"].lower()
            except:
                self.exception_occurred = True
        return Milter.CONTINUE

    def eoh(self):
        if (
            self.exception_occurred
            or self.domain is None
            or self.sdid is None
            or not self.signedfrom
            or self.domain != self.sdid
        ):
            # For the meaning of 554 see RFC5321 "4.2 SMTP
            # Replies". For the meaning of 5.7.0 see RFC3463.
            self.setreply(
                "554",
                "5.7.0",
                "Sender address rejected: Domain not matching DKIM SDID.",
            )
            return Milter.REJECT
        else:
            return Milter.ACCEPT


def main():
    addr = f"inet:{CG_SDIDMILTER_PORT}@localhost"
    timeout = 10
    Milter.factory = CompareRFC5322FromToDKIMSDID
    Milter.runmilter("sdidmilterd", addr, timeout)


if __name__ == "__main__":
    main()
