from typing import Optional

from pydantic import BaseModel, Field


class CubeSchema(BaseModel):
    service_name: str = Field(...)
    server_ip: str = Field(...)
    server_port: str = Field(...)

class CubePutModel(BaseModel):
    info     :CubeSchema
    
class CubeGetModel(BaseModel): 
    info     :CubeSchema
    message  :str 

