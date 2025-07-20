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

from os import getenv

DB_URL = "postgresql+psycopg://gauss@localhost:5432/communalgrowth-database"
FQDN = "communalgrowth.org"
CG_IMAP_PWD_FILE = getenv("CG_IMAP_PWD_FILE") or ""
CG_TLS_DIR = getenv("CG_TLS_DIR") or ""
# Port to run the quota policy server in.
CG_POLICY_PORT = getenv("CG_POLICY_PORT") or ""

# How many document IDs per e-mail are processed.
RATELIMIT_DOCIDS = 20
