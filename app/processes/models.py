str_description = """
    The data models/schemas for workflow operations.
"""

from    pydantic            import BaseModel, Field
from    typing              import Optional, List, Dict
from    datetime            import datetime
from    enum                import Enum

class State(Enum):
    NOT_STARTED      = 0
    RETRIEVED        = 1
    PUSHED           = 2
    REGISTERED       = 3
    FEED_CREATED     = 4
    WORKFLOW_STARTED = 5

class DicomThenSchema(BaseModel):
    """A model returned when an async PACS directive is indicated"""
    db                       : str   = ""
    swift                    : str   = ""
    swiftServicesPACS        : str   = ""                          
    swiftPackEachDICOM       : bool  = True  
    CUBE                     : str   = ""
    parseAllFilesWithSubStr  : str   = ""
    
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
    
class PACSqueryCore(BaseModel):
    """The PACS Query model"""
    AccessionNumber                     : str   = ""
    PatientID                           : str   = ""
    PatientName                         : str   = ""
    PatientBirthDate                    : str   = ""
    PatientAge                          : str   = ""
    PatientSex                          : str   = ""
    StudyDate                           : str   = ""
    StudyDescription                    : str   = ""
    StudyInstanceUID                    : str   = ""
    Modality                            : str   = ""
    ModalitiesInStudy                   : str   = ""
    PerformedStationAETitle             : str   = ""
    NumberOfSeriesRelatedInstances      : str   = ""
    InstanceNumber                      : str   = ""
    SeriesDate                          : str   = ""
    SeriesDescription                   : str   = ""
    SeriesInstanceUID                   : str   = ""
    ProtocolName                        : str   = ""
    AcquisitionProtocolDescription      : str   = ""
    AcquisitionProtocolName             : str   = ""
        
class DicomStatusQuerySchema(BaseModel):
    """The Dicom status Query model"""
    PFDCMservice                        : str   = ""
    PACSservice                         : str   = ""
    PACSdirective                       : PACSqueryCore
    dblogbasepath                       : str   = ""
    FeedName                            : str  = "" 
    User                                : str  = "" 

class DicomActionQuerySchema(BaseModel):
    """The Dicom status Query model"""
    PFDCMservice                        : str   = ""
    PACSservice                         : str   = ""
    PACSdirective                       : PACSqueryCore
    dblogbasepath                       : str   = ""
    thenArgs                            : DicomThenSchema
    feedArgs                            : DicomFeedQuerySchema
    
class DicomStatusResponseSchema(BaseModel):
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
    WorkflowState                       : str  = State.NOT_STARTED.name
    Stale                               : bool = True
    Started                             : bool = False
    
    
class WorkflowSchema(BaseModel):
    key                                 : str  = ""
    request                             : DicomStatusQuerySchema
    status                              : DicomStatusResponseSchema
        
class time(BaseModel):
    """A simple model that has a time string field"""
    time            : str

class PACSqueyReturnModel(BaseModel):
    """
    A full model that is returned from a query call
    """
    response        : dict

# Some "helper" classes
class ValueStr(BaseModel):
    value           : str = "" 

def ResponseModel(message):
    return {
        "code": 200,
        "message": message,
    }
