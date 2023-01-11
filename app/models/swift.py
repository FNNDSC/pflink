from typing import Optional

from pydantic import BaseModel, Field


class SwiftSchema(BaseModel):
    swift_key: str = Field(...)
    swift_services_pacs   : str = Field(...)

    

def SwiftPutModel(data):
    info     :data
    
def SwiftGetModel(data,message): 
    return {
            "data"     :data,
            "code"     :200,
            "message"  :message,
            }
    
def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
