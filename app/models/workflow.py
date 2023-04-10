str_description = """
    The data models/schemas for workflow operations.
"""

from    pydantic            import BaseModel, Field
from    typing              import Optional, List, Dict
from    datetime            import datetime
from    enum                import Enum

class State(Enum):
    INITIALIZING                         = 0
    RETRIEVING                           = 1
    PUSHING                              = 2
    REGISTERING                          = 3
    FEED_CREATED                         = 4
    ANALYZING                            = 5
    COMPLETED                            = 6
    
class Error(Enum):
    pfdcm                                = "PFDCM server is unavailable."                                                                              
    study                                = "Study not found in the PACS server. Please enter valid study info."                                          
    feed                                 = "Error creating new feed."
    analysis                             = "Error creating new analysis."                                
    compute                              = "Analysis failed."
    cube                                 = "CUBE server is unavailable."
    

class DicomThenSchema(BaseModel):
    """PFDCM specific params"""
    db                                  : str  = ""
    swift                               : str  = ""
    swiftServicesPACS                   : str  = ""                          
    swiftPackEachDICOM                  : bool = True  
    CUBE                                : str  = ""
    parseAllFilesWithSubStr             : str  = ""
    
class TestArgs(BaseModel):
    GetError                            : str = ""
    
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
    testArgs                            : TestArgs
    
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
                },
                "testArgs": {
                  "GetError": ""
                }
              }
        }         
        
class DicomStatusResponseSchema(BaseModel):
    """The Workflow status response Model"""
    Status                              : bool = True
    WorkflowState                       : str  = State.INITIALIZING.name
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

