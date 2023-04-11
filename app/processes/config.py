from pydantic import BaseSettings, MongoDsn, AnyHttpUrl


class Settings(BaseSettings):
    pfdcm_name: str = 'PFDCMLOCAL'
    pflink_mongodb: MongoDsn = 'mongodb://localhost:27017'
    pflink_pfdcm: AnyHttpUrl = 'http://localhost:4005'
    pflink_port: int = 8050
    version: str = "2.0.2"


settings = Settings()
