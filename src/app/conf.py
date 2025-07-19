from os import getenv

DB_URL = "postgresql+psycopg://gauss@localhost:5432/communalgrowth-database"
FQDN = "communalgrowth.org"
CG_IMAP_PWD_FILE = getenv("CG_IMAP_PWD_FILE") or ""
CG_TLS_DIR = getenv("CG_TLS_DIR") or ""
# Port to run the quota policy server in.
CG_POLICY_PORT = getenv("CG_POLICY_PORT") or ""

# How many document IDs per e-mail are processed.
RATELIMIT_DOCIDS = 20
