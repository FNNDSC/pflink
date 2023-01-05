from typing import Optional

from pydantic import BaseModel, Field


class CubeSchema(BaseModel):
    service_name: str = Field(...)
    server_ip   : str = Field(...)
    server_port : str = Field(...)

def CubePutModel(data):
    info     :data
    
def CubeGetModel(data,message): 
    return {
            "data"     :data,
            "code"     :200,
            "message"  :message,
            }
    
def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}

