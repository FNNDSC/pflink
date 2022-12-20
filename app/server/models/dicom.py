from typing import Optional

from pydantic import BaseModel, Field


class DicomSchema(BaseModel):
    seriesID: str = Field(...)
    studyID: str = Field(...)



    class Config:
        schema_extra = {
            "example": {
                "seriesID": "1234",
                "studyID": "1234",

            }
        }


class UpdateDicomModel(BaseModel):
    seriesID: Optional[str]
    studyID: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "seriesID": "1234",
                "studyID": "1234",
            }
        }


def ResponseModel(data, message):
    return {
        "data": [data],
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}

