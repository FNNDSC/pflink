str_description = """
    The data models/schemas for DICOM operations.
"""

from    pydantic            import BaseModel, Field
from    typing              import Optional, List, Dict
from    datetime            import datetime

class DicomThenSchema(BaseModel):
    """A model returned when an async PACS directive is indicated"""
    db                       : str   = ""
    swift                    : str   = ""
    swiftServicesPACS        : str   = ""                          
    swiftPackEachDICOM       : bool  = True  
    CUBE                     : str   = ""
    parseAllFilesWithSubStr  : str   = ""
    
class DicomFeedQuerySchema(BaseModel):
    FeedName                            : str  = "" 
    User                                : str  = "" 
    Pipeline                            : str  = ""
        
class DicomStatusQuerySchema(BaseModel):
    """The Dicom status Query model"""
    PFDCMservice                        : str   = ""
    PACSservice                         : str   = ""
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
    dblogbasepath                       : str   = ""
    feedArgs                            : DicomFeedQuerySchema

class DicomActionQuerySchema(BaseModel):
    """The Dicom status Query model"""
    PFDCMservice                        : str   = ""
    PACSservice                         : str   = ""
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
    dblogbasepath                       : str   = ""
    thenArgs                            : DicomThenSchema
    feedArgs                            : DicomFeedQuerySchema
    
class DicomStatusResponseSchema(BaseModel):
    StudyFound                          : bool = False
    Retrieved                           : str  = ""
    Pushed                              : str  = ""
    Registered                          : str  = ""
    FeedCreated                         : bool = False
    FeedName                            : str  = ""
    WorkflowStarted                     : bool = False
    FeedProgress                        : str  = ""
    FeedStatus                          : str  = ""
    Message                             : str  = ""
    Error                               : str  = ""
        
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
