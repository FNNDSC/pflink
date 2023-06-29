from pydantic import BaseModel, Field


class Plugin(BaseModel):
    """This class represents a CUBE plugin"""
    name: str = Field(...)
    version: str = Field(...)




