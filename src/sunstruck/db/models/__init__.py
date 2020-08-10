""" Database table definitions """

# flake8: noqa
from db.models.bases import Base as Model
from db.models.bases import BaseTable, db
from db.models.clients import OAuth2Client
from db.models.users import User
