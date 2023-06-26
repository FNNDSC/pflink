from pydantic import BaseModel, Field
from typing import List


class PluginParam(BaseModel):
    """This class represents a plugin param"""
    name: str = ""
    default: object = ""


class Plugin(BaseModel):
    """This class represents a CUBE plugin"""
    name: str = Field(...)
    version: str = Field(...)
    params: List[PluginParam] = []




