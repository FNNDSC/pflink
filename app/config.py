from pydantic import BaseSettings, MongoDsn


class Settings(BaseSettings):
    pflink_mongodb: MongoDsn = 'mongodb://localhost:27017'
    version: str = "4.0.0"
    mongo_username: str = "admin"
    mongo_password: str = "admin"
    log_level: str = "DEBUG"
    delay: int = 0


class Auth(BaseSettings):
    JWT_SECRET_KEY: str = "aad10a452df3f4451c975a0a2982b159c5088eb0f5da816a1fb129f473c0ddc7"  # should be kept secret
    user_name: str = 'pflink'
    password: str = 'pflink1234'

settings = Settings()
auth = Auth()
