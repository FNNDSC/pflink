from typing import Optional

from pydantic import BaseModel, Field


class PfdcmSchema(BaseModel):
    service_name: str = Field(...)
    server_ip: str = Field(...)
    server_port: str = Field(...)

class PfdcmPutModel(BaseModel):
    info     :PfdcmSchema
    
class PfdcmGetModel(BaseModel): 
    info     :PfdcmSchema
    message  :str 

