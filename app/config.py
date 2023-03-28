from pydantic import BaseSettings


class Settings(BaseSettings):
    MONGO_DETAILS: str = "mongodb://localhost:27017"
    PFDCM_DETAILS: str = 'http://localhost:4005'
    PORT: int = 8050


settings = Settings()
