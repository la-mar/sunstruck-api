from db.models.bases import BaseTable, db

__all__ = ["TestModel"]


class TestModel(BaseTable):
    __tablename__ = "test"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.EmailType, nullable=False)
    is_active = db.Column(db.Boolean(), default=True)
    is_superuser = db.Column(db.Boolean(), default=False)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    phone_number = db.Column(db.Unicode(20))
    country_code = db.Column(db.Unicode(20))
    hashed_password = db.Column(db.String())
    uq_username = db.UniqueConstraint("username")
    uq_email = db.UniqueConstraint("email")
    ix_username = db.Index("ix_test_username", "username")
    ix_email = db.Index("ix_test_email", "email")
