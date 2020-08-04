import pytest

from schemas.database_url import DatabaseURL


@pytest.fixture
def db_conf():
    db_conf: DatabaseURL = DatabaseURL(
        drivername="postgresql+asyncpg",
        username="user",
        password="pass",
        host="localhost",
        port=5432,
        database="dbname",
    )
    yield db_conf


class TestDatabaseURL:
    def test_build_from_components(self, db_conf):
        expected = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
        assert str(db_conf.url) == expected

    def test_idempotency(self, db_conf):
        x = DatabaseURL(**db_conf.dict())
        assert db_conf.dict() == x.dict()
