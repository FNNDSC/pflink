from pydantic import BaseModel, Field, validator
from typing import List


class Plugin(BaseModel):
    """This class represents a CUBE plugin"""
    name: str = Field(...)
    version: str = Field(...)


class CubeService(BaseModel):
    """This class represents a CUBE service"""
    service_name: str = Field(...)
    service_URL: str = Field(...)

    @validator('*')
    def check_for_empty_string(cls, v):
        assert v != '', "Empty strings not allowed."
        return v


class CubeServiceResponse(BaseModel):
    """This class represents a CUBE service response from `pflink`"""
    data: dict
    message: str = ""


class CubeServiceCollection(BaseModel):
    """This class represents the collection of CUBE services available"""
    data: List[str]
    message: str = ""
