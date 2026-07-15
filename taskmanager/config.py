import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = "sqlite:///tasks.db"
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('email')
    MAIL_PASSWORD = os.environ.get('password')
    JWT_SECRET_KEY = os.environ.get("JWT_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)