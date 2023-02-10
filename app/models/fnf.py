from pydantic import BaseModel, Field
from enum import Enum

class State(Enum):
    INIT = 1
    PROGRESS = 2
    FINISHED = 3

class FnfRequestSchema(BaseModel):
    foo: str = ""
    bar: str = ""
    oof: str = ""
    rab: str = ""
    
class FnfResponseSchema(BaseModel):
    taskProgress : int = 0
    taskState : str = State.INIT.name
    stale: bool = True
    started: bool = False
    
class FnfWorkflowSchema(BaseModel):
    key: str = ""
    request: FnfRequestSchema 
    response: FnfResponseSchema
