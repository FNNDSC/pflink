from typing import Optional

from pydantic import BaseModel, Field


class PfdcmSchema(BaseModel):
    service_name: str = Field(...)
    server_ip   : str = Field(...)
    server_port : str = Field(...)
    
class PfdcmQuerySchema(BaseModel):
    PFDCMservice: str = ""
    
class PfdcmQueryReturnModel(BaseModel):
    response: dict

def PfdcmPutModel(data):
    info     :data
    
def PfdcmGetModel(data,message): 
    return {
            "data"     :data,
            "code"     :200,
            "message"  :message,
            }
    
def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
