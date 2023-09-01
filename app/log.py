from app.config import settings
log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": '%(log_color)s {"worker":"%(workername)16s", "timestamp":"%('
                       'asctime)s", "key":"%(key)s", "%(levelname)-8s":"%(message)s"}\33[0m',
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
            "pflink-logger": {"handlers": ["default"], "level": settings.log_level},
        },
    }