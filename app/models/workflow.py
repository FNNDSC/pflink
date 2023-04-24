from pydantic import BaseModel, Field
from enum import Enum

str_description = """
    The data models/schemas for workflow operations.
"""


class State(Enum):
    """This Enum represents all the possible states of a workflow"""
    INITIALIZING = "initializing workflow"
    RETRIEVING = "retrieving from PACS"
    PUSHING = "pushing to swift"
    REGISTERING = "registering to CUBE"
    FEED_CREATED = "feed created"
    ANALYZING = "analyzing study"
    COMPLETED = "completed"


class Error(Enum):
    """This Enum represents all the possible errors in a workflow"""
    pfdcm = "PFDCM server is unavailable."
    study = "Study not found in the PACS server. Please enter valid study info."
    feed = "Error creating new feed."
    analysis = "Error creating new analysis."
    compute = "Analysis failed."
    cube = "CUBE server is unavailable."
    status = "Error occurred while updating workflow status."
    user = "Error while creating a user."
    PACS = "Error while connecting to PACS server."
    required_pfdcm = "Please provide a pfdcm service name."
    required_PACS = "Please provide a PACS service name."
    required_directive = "Please enter at least one value in PACS_directive"
    required_feed = "Please provide a feed name."
    required_user = "Please provide a user name."
    required_plugin = "Please provide a plugin name."
    undefined = "Please enter a valid error type."


class PFDCMInfoSchema(BaseModel):
    """This model contains service details of a pfdcm instance"""
    pfdcm_service: str = Field(...)
    PACS_service: str = Field(...)
    cube_service: str = "local"
    swift_service: str = "local"
    dicom_file_extension: str = "dcm"
    db_log_path: str = "/home/dicom/log"


class WorkflowInfoSchema(BaseModel):
    """This schema includes all the information to create a new workflow in CUBE"""
    feed_name: str = Field(...)
    user_name: str = Field(...)
    plugin_name: str = Field(...)
    plugin_version: str = Field(...)
    plugin_params: str = ""
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
    PACS_directive: PACSqueryCore
    workflow_info: WorkflowInfoSchema

    class Config:
        schema_extra = {
            "example": {
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
    error: str = ""


class WorkflowDBSchema(BaseModel):
    """The DB model of a workflow object"""
    key: str = ""
    request: WorkflowRequestSchema
    response: WorkflowStatusResponseSchema
    stale: bool = True
    started: bool = False

