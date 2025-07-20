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

import re


def splitlines_clean(s):
    """Split lines, removing surrounding spaces, and empty or blank lines"""
    return [x.strip() for x in s.splitlines() if x and not x.isspace()]


def strip_to_alphanum(s):
    """Remove all non-alphanumeric characters from s, keep spaces and single quote"""
    r = re.compile(r"[^\w\s']|_", re.UNICODE)
    return r.sub("", s)


def parse_pgpass(path):
    """Parse a .pgpass PostgreSQL file

    Returns the required connection string.

    TODO remove this function once
    <https://github.com/nginx/unit/issues/1455> is fixed.
    """
    with open(path, "r") as f:
        line = f.readline().rstrip()
    host, port, db, user, password = line.split(":")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
