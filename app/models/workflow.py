import datetime
import pytz
from pydantic import BaseModel, Field, ValidationError, validator
from enum import Enum
from app.models.auth import User

str_description = """
    The data models/schemas for workflow operations.
"""


class State(str, Enum):
    """This Enum represents all the possible states of a workflow"""
    INITIALIZING = "initializing workflow"
    RETRIEVING = "retrieving from PACS"
    PUSHING = "pushing to swift"
    REGISTERING = "registering to CUBE"
    FEED_CREATED = "feed created"
    ANALYZING = "analyzing study"
    COMPLETED = "completed"
    FEED_DELETED = "feed deleted from CUBE"
    DUPLICATE_REQUEST = "duplicate workflow exists"


class Error(str, Enum):
    """This Enum represents all the possible errors in a workflow"""
    pfdcm = "PFDCM server is unavailable. "
    study = "Study not found in the PACS server. Please provide a valid study info. "
    feed = "Error creating new feed. "
    analysis = "Error creating new analysis. "
    compute = "Analysis failed. "
    cube = "Error while connecting to CUBE. "
    status = "Error while updating workflow status. "
    user = "Error while creating a user. "
    PACS = "Error while connecting to PACS server. "
    required_directive = "Please enter at least one value in PACS_directive."
    required_field = "Empty strings not allowed."
    undefined = "Please enter a valid error type."
    feed_deleted = "Feed deleted from CUBE. Please change the feed name and re-submit the request."


class PFDCMInfoSchema(BaseModel):
    """This model contains service details of a pfdcm instance"""
    pfdcm_service: str = Field(...)
    PACS_service: str = Field(...)
    cube_service: str = "local"
    swift_service: str = "local"
    dicom_file_extension: str = "dcm"
    db_log_path: str = "/home/dicom/log"

    @validator('*')
    def check_for_empty_string(cls, v):
        assert v != '', Error.required_field.value
        return v


class WorkflowInfoSchema(BaseModel):
    """This schema includes all the information to create a new workflow in CUBE"""
    feed_name: str = Field(...)
    plugin_name: str = ""
    plugin_version: str = ""
    plugin_params: str = ""
    pipeline_name: str = ""

    @validator('feed_name')
    def check_for_empty_string(cls, v):
        assert v != '', Error.required_field.value
        return v


class PACSqueryCore(BaseModel):
    """The PACS Query model"""
    AccessionNumber: str = ""
    PatientID: str = ""
    PatientName: str = ""
    PatientBirthDate: str = ""
    PatientAge: str = ""
    PatientSex: str = ""
    StudyDate: str = ""
    StudyDescription: str = ""
    StudyInstanceUID: str = ""
    Modality: str = ""
    ModalitiesInStudy: str = ""
    PerformedStationAETitle: str = ""
    NumberOfSeriesRelatedInstances: str = ""
    InstanceNumber: str = ""
    SeriesDate: str = ""
    SeriesDescription: str = ""
    SeriesInstanceUID: str = ""
    ProtocolName: str = ""
    AcquisitionProtocolDescription: str = ""
    AcquisitionProtocolName: str = ""


class WorkflowRequestSchema(BaseModel):
    """The Workflow Request model"""
    ignore_duplicate: bool = True
    pfdcm_info: PFDCMInfoSchema
    PACS_directive: PACSqueryCore
    workflow_info: WorkflowInfoSchema
    cube_user_info: User

    @validator('PACS_directive')
    def check_if_one_present(cls, value):
        count = 0
        for k, v in value:
            if v:
                count += 1
        assert count != 0, Error.required_directive.value
        return value

    class Config:
        schema_extra = {
            "example": {
                "ignore_duplicate": True,
                "pfdcm_info": {
                    "pfdcm_service": "PFDCM",
                    "PACS_service": "orthanc"
                },
                "PACS_directive": {
                    "StudyInstanceUID": "12365548",
                    "SeriesInstanceUID": "66498598"
                },
                "workflow_info": {
                    "feed_name": "test-%SeriesInstanceUID",
                    "plugin_name": "pl-simpledsapp",
                    "plugin_version": "2.1.0",
                    "plugin_params": "--args ARGS"
                },
                "cube_user_info": {
                    "username": "chris",
                    "password": "chris1234"
                }
            }
        }


class UserResponseSchema(BaseModel):
    """A model to display username along with a response for its workflow request"""
    username: str = ""
    response: dict


class WorkflowStatusResponseSchema(BaseModel):
    """The Workflow status response model"""
    status: bool = True
    workflow_state: State = State.INITIALIZING
    state_progress: str = "0%"
    feed_id: str = ""
    feed_name: str = ""
    message: str = ""
    duplicates: list[UserResponseSchema] = None
    error: str = ""
    workflow_progress_perc: int = 0


class WorkflowDBSchema(BaseModel):
    """The DB model of a workflow object"""
    key: str = ""
    fingerprint: str = ""
    creation_time: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    request: WorkflowRequestSchema
    response: WorkflowStatusResponseSchema
    service_retry: int = 5
    stale: bool = True
    started: bool = False


class WorkflowSearchSchema(BaseModel):
    """A schema to search Workflow DB records"""
    keywords: str = ""
