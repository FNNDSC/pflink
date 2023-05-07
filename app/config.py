from typing import Any

from pydantic import BaseSettings, MongoDsn


class Settings(BaseSettings):
    pflink_mongodb: MongoDsn = 'mongodb://localhost:27017'
    version: str = "3.0.1"


class User(BaseSettings):
    user_name: str = 'chris'
    password: str = 'chris1234'


class Auth(BaseSettings):
    JWT_SECRET_KEY = "aad10a452df3f4451c975a0a2982b159c5088eb0f5da816a1fb129f473c0ddc7"  # should be kept secret


settings = Settings()
user = User()
auth = Auth()
