from pydantic import BaseSettings, MongoDsn


class Settings(BaseSettings):
    pflink_mongodb: MongoDsn = 'mongodb://localhost:27017'
    version: str = "2.2.0"


settings = Settings()

