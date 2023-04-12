from pydantic import BaseModel, Field
from enum import Enum

str_description = """
    The data models/schemas for workflow operations.
"""


class State(Enum):
    """This Enum represents all the possible states of a workflow"""
    INITIALIZING = "initializing"
    RETRIEVING = "retrieving"
    PUSHING = "pushing"
    REGISTERING = "registering"
    FEED_CREATED = "feed created"
    ANALYZING = "analyzing"
    COMPLETED = "completed"


class Error(Enum):
    """This Enum represents all the possible errors in a workflow"""
    pfdcm = "PFDCM server is unavailable."
    study = "Study not found in the PACS server. Please enter valid study info."
    feed = "Error creating new feed."
    analysis = "Error creating new analysis."
    compute = "Analysis failed."
    cube = "CUBE server is unavailable."


class PFDCMInfoSchema(BaseModel):
    """This model contains service details of a pfdcm instance"""
    pfdcm_service: str = Field(...)
    pacs_service: str = Field(...)
    cube_service: str = Field(...)
    db_log_path: str = Field(...)


class WorkflowInfoSchema(BaseModel):
    feed_name: str = Field(...)
    user_name: str = Field(...)
    plugin_name: str = Field(...)
    plugin_version: str = Field(...)
    plugin_params: str = Field(...)
    cred_in_params: bool = False
    pipeline_name: str = ""


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
    pfdcm_info: PFDCMInfoSchema
    pacs_directive: PACSqueryCore
    workflow_info: WorkflowInfoSchema

    class Config:
        schema_extra = {
            "example":{
                "pfdcm_info": {
                    "pfdcm_service": "PFDCM",
                    "pacs_service": "orthanc",
                    "cube_service": "local",
                    "db_log_path": "/home/dicom/log"
                },
                "pacs_directive": {
                    "StudyInstanceUID": "12365548",
                    "SeriesInstanceUID": "66498598"
                },
                "workflow_info": {
                    "feed_name": "test-%SeriesInstanceUID",
                    "user_name": "clinical_user",
                    "plugin_name": "pl-dircopy",
                    "plugin_version": "1.1.0",
                    "plugin_params": "--args ARGS"
                }
            }
        }

        
class WorkflowStatusResponseSchema(BaseModel):
    """The Workflow status response model"""
    status: bool = True
    workflow_state: str = State.INITIALIZING.value
    state_progress: str = "0%"
    feed_id: str = ""
    feed_name: str = ""
    message: str = ""
    error: str = ""


class WorkflowDBSchema(BaseModel):
    """The DB model of a workflow object"""
    key: str = ""
    request: WorkflowRequestSchema
    response: WorkflowStatusResponseSchema
    stale: bool = True
    started: bool = False
