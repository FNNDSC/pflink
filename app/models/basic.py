from pydantic import BaseModel, Field


class AboutModel(BaseModel):
    """
    This model represents basic details about this application
    """
    name: str = Field(..., title='Name of application', example="MyAwesomeApp")
    about: str = Field(..., title='About this application', example="My awesome app does awesome things")
    version: str = Field(..., title='Version string', example="1.0.0")
