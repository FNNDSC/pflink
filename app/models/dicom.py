str_description = """
    The data models/schemas for the PACS QR collection.
"""

from    pydantic            import BaseModel, Field
from    typing              import Optional, List, Dict
from    datetime            import datetime


class DicomQuerySchema(BaseModel):
    """The PACS Query model"""
    StudyInstanceUID                    : str   = ""
    SeriesInstanceUID                   : str   = ""
    then                                : str   = ""
    thenArgs                            : str   = ""
class PACSasync(BaseModel):
    """A model returned when an async PACS directive is indicated"""
    directiveType                       : str   = "async"
    response                            : dict
    timestamp                           : str
    PACSdirective                       : dict

class time(BaseModel):
    """A simple model that has a time string field"""
    time            : str

class PACSqueyReturnModel(BaseModel):
    """
    A full model that is returned from a query call
    """
    response        : dict

# Some "helper" classes
class ValueStr(BaseModel):
    value           : str = "" 

def ResponseModel(message):
    return {
        "code": 200,
        "message": message,
    }
