from typing import Optional,List
from fastapi    import APIRouter, Query
from pydantic import BaseModel, Field

class ValueStr(BaseModel):
    value:              str         = ""

def helloRouter_create(
        name:       str,
        about:      str,
        version:    str,
        tags:       List[str] = None
    ) -> APIRouter:
    if tags is None:
        tags = ['pflink environmental detail']

    about_name      = name
    about_about     = about
    about_version   = version

    class AboutModel(BaseModel):
        name:       str = Field(about_name,     title='Name of application')
        about:      str = Field(about_about,    title='About this application')
        version:    str = Field(about_version,  title='Version string')

    about_model = AboutModel()
    return about_model


