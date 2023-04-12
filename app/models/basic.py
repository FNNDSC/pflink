from pydantic import BaseModel, Field


class AboutModel(BaseModel):
    name: str = Field(..., title='Name of application')
    about: str = Field(..., title='About this application')
    version: str = Field(..., title='Version string')
