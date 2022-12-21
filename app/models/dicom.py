from typing import Optional

from pydantic import BaseModel, Field


class DicomSchema(BaseModel):
    series_id: str = Field(...)
    study_id: str = Field(...)


    class Config:
        schema_extra = {
            "example": {
                "series_id": "1.2.3.4",
                "study_id": "5.6.7.8",

            }
        }


class UpdateDicomModel(BaseModel):
    series_id: Optional[str]
    study_id: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "series_id": "1.2.3.4",
                "study_id": "5.6.7.8",
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


