str_description = """
    The data models/schemas for workflow operations.
"""

from    pydantic            import BaseModel, Field
from    typing              import Optional, List, Dict
from    datetime            import datetime
from    enum                import Enum

class State(Enum):
    STARTED                              = 0
    RETRIEVED                            = 1
    PUSHED                               = 2
    REGISTERED                           = 3
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
    Params                              : dict
    PassUserCreds                       : bool = False
    
class DicomFeedQuerySchema(BaseModel):
    FeedName                            : str  = "" 
    User                                : str  = "" 
    Pipeline                            : str  = ""
    nodeArgs                            : WorkflowPluginInstanceSchema

class TestSchema(BaseModel):
    Testing                             : bool = False
    CurrentState                        : str  = ""
        
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
    testArgs                            : TestSchema 

class DicomStatusResponseSchema(BaseModel):
    """The Workflow status response Model"""
    WorkflowState                       : str  = State.STARTED.name
    StudyFound                          : bool = False
    Retrieved                           : str  = "0%"
    Pushed                              : str  = "0%"
    Registered                          : str  = "0%"
    FeedId                              : str  = ""
    FeedName                            : str  = ""
    FeedProgress                        : str  = "0%"
    FeedStatus                          : str  = ""
    Message                             : str  = ""
    Error                               : str  = ""    
    Stale                               : bool = True
    Started                             : bool = False
    
    
class WorkflowSchema(BaseModel):
    key                                 : str  = ""
    request                             : DicomStatusQuerySchema
    status                              : DicomStatusResponseSchema
        

        
