# from db.models.bases import Base, db

# __all__ = ["User"]


# class User(Base):
#     __tablename__ = "users"
#     id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     first_name = db.Column(db.String(255))
#     last_name = db.Column(db.String(255))
#     email = db.Column(db.String())
#     phone_number = db.Column(db.Unicode(20))
#     country_code = db.Column(db.Unicode(20))

#     uq_email = db.UniqueConstraint("email")
