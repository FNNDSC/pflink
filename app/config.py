from pydantic import BaseSettings, MongoDsn


class Settings(BaseSettings):
    pflink_mongodb: MongoDsn = 'mongodb://localhost:27017'
    version: str = "2.1.6"


settings = Settings()

