from pydantic import BaseModel, Field
from enum import Enum

State = Enum('State',['INIT', 'PROG', 'FIN'])

class FnfSchema(BaseModel):
    foo: str = ""
    bar: str = ""
    oof: str = ""
    rab: str = ""
    
class FnfResponseSchema(BaseModel):
    taskProgress : int = 0
    taskState : int = 0
    stale: bool = True
    started: bool = False
    
class FnfWorkflowSchema(BaseModel):
    key: str = ""
    request: dict 
    response: dict
