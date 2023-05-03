from typing import Any

from pydantic import BaseSettings, MongoDsn


class Settings(BaseSettings):
    pflink_mongodb: MongoDsn = 'mongodb://localhost:27017'
    version: str = "2.1.9"


class User(BaseSettings):
    user_name: str = 'chris'
    password: str = 'chris1234'


settings = Settings()
user = User()
