str_description = """
    The data models/schemas for workflow operations.
"""

from    pydantic            import BaseModel, Field
from    typing              import Optional, List, Dict
from    datetime            import datetime
from    enum                import Enum

class State(Enum):
    STARTED                              = 0
    RETRIEVING                           = 1
    PUSHING                              = 2
    REGISTERING                          = 3
    FEED_CREATED                         = 4
    ANALYSIS_STARTED                     = 5
    COMPLETED                            = 6

class DicomThenSchema(BaseModel):
    """A model returned when an async PACS directive is indicated"""
    db                                  : str  = ""
    swift                               : str  = ""
    swiftServicesPACS                   : str  = ""                          
    swiftPackEachDICOM                  : bool = True  
    CUBE                                : str  = ""
    parseAllFilesWithSubStr             : str  = ""
    
class WorkflowPluginInstanceSchema(BaseModel):
    PluginName                          : str  = ""
    Version                             : str  = ""
    Params                              : str  = ""
    PassUserCreds                       : bool = False
    
class DicomFeedQuerySchema(BaseModel):
    FeedName                            : str  = "" 
    User                                : str  = "" 
    Pipeline                            : str  = ""
    nodeArgs                            : WorkflowPluginInstanceSchema
        
class PACSqueryCore(BaseModel):
    """The PACS Query model"""
    AccessionNumber                     : str  = ""
    PatientID                           : str  = ""
    PatientName                         : str  = ""
    PatientBirthDate                    : str  = ""
    PatientAge                          : str  = ""
    PatientSex                          : str  = ""
    StudyDate                           : str  = ""
    StudyDescription                    : str  = ""
    StudyInstanceUID                    : str  = ""
    Modality                            : str  = ""
    ModalitiesInStudy                   : str  = ""
    PerformedStationAETitle             : str  = ""
    NumberOfSeriesRelatedInstances      : str  = ""
    InstanceNumber                      : str  = ""
    SeriesDate                          : str  = ""
    SeriesDescription                   : str  = ""
    SeriesInstanceUID                   : str  = ""
    ProtocolName                        : str  = ""
    AcquisitionProtocolDescription      : str  = ""
    AcquisitionProtocolName             : str  = ""
        
class DicomStatusQuerySchema(BaseModel):
    """The Workflow status Query model"""
    PFDCMservice                        : str  = ""
    PACSservice                         : str  = ""
    PACSdirective                       : PACSqueryCore
    thenArgs                            : DicomThenSchema
    dblogbasepath                       : str  = ""
    FeedName                            : str  = "" 
    User                                : str  = ""
    analysisArgs                        : WorkflowPluginInstanceSchema 
    
    class Config:
        schema_extra = {
            "example": {
                "PFDCMservice": "PFDCMLOCAL",
                "PACSservice": "orthanc",
                "PACSdirective": {
                  "PatientID": "12345",
                  "StudyInstanceUID": "78441995125526",
                  "SeriesInstanceUID": "1546579521526"
                },
                "thenArgs": {
                  "db": "/home/dicom/log",
                  "swift": "local",
                  "swiftServicesPACS": "orthanc",
                  "swiftPackEachDICOM": True,
                  "CUBE": "local",
                  "parseAllFilesWithSubStr": "dcm"
                },
                "dblogbasepath": "/home/dicom/log",
                "FeedName": "test-%SeriesInstanceUID",
                "User": "cl_user_2",
                "analysisArgs": {
                  "PluginName": "pl-test_plugin",
                  "Version": "1.1.0",
                  "Params": "",
                  "PassUserCreds": False
                }
              }
        }         
        
class DicomStatusResponseSchema(BaseModel):
    """The Workflow status response Model"""
    StudyFound                          : bool = False
    WorkflowState                       : str  = State.STARTED.name
    StateProgress                       : str  = "0%"
    FeedId                              : str  = ""
    FeedName                            : str  = ""
    CurrentNode                         : list = []
    Message                             : str  = ""
    Error                               : str  = ""  
    
class WorkflowSchema(BaseModel):
    key                                 : str  = ""
    request                             : DicomStatusQuerySchema
    status                              : DicomStatusResponseSchema
    Stale                               : bool = True
    Started                             : bool = False

