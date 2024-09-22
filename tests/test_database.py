import subprocess
import time
import pytest
import psycopg
import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.orm

from app.cgdb import Base

COMPOSEFILE = "./tests/containers/postgresql.yml"

pytestmark = [pytest.mark.test_online, pytest.mark.test_slow]


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
    yield db_url
    # Comment out the line below if you don't want the test to clean
    # up the database. The database must be then manually be cleaned
    # up with:
    # podman-compose -f tests/containers/postgresql.yml down -t0
    # subprocess.run(["podman-compose", "-f", COMPOSEFILE, "down", "-t0"])


def test_postgresql(postgresql):
    engine = sqlalchemy.create_engine(
        postgresql,
        # Pool size may be adjusted if multiple tests ran
        # concurrently, say via `pytest -n auto`.
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    with Session() as session:
        session.commit()
