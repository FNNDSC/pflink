from pydantic import BaseSettings, MongoDsn


class Settings(BaseSettings):
    pflink_mongodb: MongoDsn = 'mongodb://localhost:27017'
    version: str = "3.7.0"
    mongo_username: str = "admin"
    mongo_password: str = "admin"


class Auth(BaseSettings):
    JWT_SECRET_KEY: str = "aad10a452df3f4451c975a0a2982b159c5088eb0f5da816a1fb129f473c0ddc7"  # should be kept secret
    user_name: str = 'pflink'
    password: str = 'pflink1234'


class LogConfig(BaseSettings):
    level: str = "DEBUG"
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": '%(log_color)s {"levelname":"%(levelname)s", "worker":"%(workername)s", "timestamp":"%('
                       'asctime)s", "key":"%(key)s", "msg":"%(message)s"}\33[0m',
                "datefmt": "%Y-%m-%d %H:%M:%S",

            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "pflink-logger": {"handlers": ["default"], "level": level},
        },
    }


settings = Settings()
auth = Auth()
log = LogConfig()
