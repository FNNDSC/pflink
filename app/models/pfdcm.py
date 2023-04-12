from pydantic import BaseModel, Field
from typing import List


class PfdcmQuerySchema(BaseModel):
    """This class represents a `pfdcm` service"""
    service_name: str = Field(..., title="A string representing the name of a `pfdcm` service", example="PFDCM")
    service_address: str = Field(..., title="Service address of the `pfdcm` instance", example="http://localhost:4005")


class PfdcmCollectionResponseModel(BaseModel):
    """pfdcm collection response model"""
    data: List[dict]
    message: str = ""


class PfdcmQueryResponseSchema(BaseModel):
    """pfdcm data response model"""
    data: dict
    message: str = ""
