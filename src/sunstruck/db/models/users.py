from db.models.bases import BaseTable, db

__all__ = ["User"]


class User(BaseTable):
    __tablename__ = "users"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.EmailType, nullable=False)
    phone_number = db.Column(db.Unicode(20))
    country_code = db.Column(db.Unicode(20))

    uq_email = db.UniqueConstraint("email")
