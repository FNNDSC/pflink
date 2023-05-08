from pydantic import BaseModel, Field, ValidationError, validator


class User(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

    @validator('username', 'password')
    def check_for_empty_string(cls, v):
        assert v != '', 'Empty strings not allowed'
        return v
