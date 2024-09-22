import subprocess
import time
import pytest
import psycopg
import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.orm

from app.cgdb import Base
from app.maildirdaemon import db_subscribe
from fixture_mail import *

COMPOSEFILE = "./tests/containers/postgresql.yml"
pytestmark = [pytest.mark.test_podman_compose, pytest.mark.test_slow]


def port_open(port):
    """Check if port is open"""
    xs = subprocess.check_output(["ss", "-tuln"], text=True).splitlines()
    for x in xs:
        if f":{port} " in x:
            return True
    return False


def podman_port(hash):
    """Find the open ports for a container"""
    xs = subprocess.check_output(["podman", "port", hash], text=True).splitlines()
    return [int(x.split(":")[1]) for x in xs]


def ensure_database_ready(db_url):
    engine = sqlalchemy.create_engine(
        db_url,
        pool_size=1,
        max_overflow=1,
        pool_pre_ping=True,
    )
    for _ in range(60):
        try:
            with engine.connect() as connection:
                connection.execute(sqlalchemy.select(1))
        except sqlalchemy.exc.OperationalError:
            time.sleep(0.5)
            pass


@pytest.fixture(scope="module")
def postgresql():
    container_hash = subprocess.check_output(
        ["podman-compose", "-f", COMPOSEFILE, "up", "--build", "-d"], text=True
    ).splitlines()[0]
    port = podman_port(container_hash)[0]
    db_url = f"postgresql+psycopg://myuser:mypassword@localhost:{port}/mydatabase"
    ensure_database_ready(db_url)
    engine = sqlalchemy.create_engine(
        db_url,
        pool_size=1,
        max_overflow=1,
        pool_pre_ping=True,
    )
    # Create the tables.
    Base.metadata.create_all(engine)
    # We yield the database URL instead of the engine because engine
    # is thread-local and we may have issues with parallel test
    # execution.
    yield db_url
    # Comment out the line below, or put a breakpoint if you don't
    # want the test to clean up the database. The database must be
    # then manually be cleaned up with:
    #     podman-compose -f tests/containers/postgresql.yml down -t0
    subprocess.run(["podman-compose", "-f", COMPOSEFILE, "down", "-t0"])


def test_db_subscribe_mail_text(postgresql, mail_text):
    mail, actual = mail_text
    engine = sqlalchemy.create_engine(
        postgresql,
        pool_size=1,
        max_overflow=1,
        pool_pre_ping=True,
    )
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    with Session() as session:
        db_subscribe(session, mail)
        session.commit()
