from os import getenv

DB_URL = "postgresql+psycopg://gauss@localhost:5432/communalgrowth-database"
FQDN = "communalgrowth.org"
CG_IMAP_PWD_FILE = getenv("CG_IMAP_PWD_FILE") or ""
