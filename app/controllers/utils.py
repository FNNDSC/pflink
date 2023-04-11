import hashlib
import json

from pymongo import MongoClient

from app.config import settings

MONGO_DETAILS = str(settings.pflink_mongodb)

client = MongoClient(MONGO_DETAILS)

database = client.workflows

workflow_collection = database.get_collection("workflows_collection")

from app.models.workflow import (
    DicomStatusQuerySchema,
    WorkflowSchema,
)

# helpers


def _workflow_retrieve_helper(workflow:dict) -> WorkflowSchema:    
    request =  DicomStatusQuerySchema(
                   PFDCMservice  = workflow["request"]["PFDCMservice"],
                   PACSservice   = workflow["request"]["PACSservice"],
                   PACSdirective = workflow["request"]["PACSdirective"],
                   thenArgs      = workflow["request"]["thenArgs"],
                   dblogbasepath = workflow["request"]["dblogbasepath"],
                   FeedName      = workflow["request"]["FeedName"],
                   User          = workflow["request"]["User"],
                   analysisArgs  = workflow["request"]["analysisArgs"],
               )
    return WorkflowSchema(
        key      = workflow["_id"],
        request  = request,
        status   = workflow["status"],
        Stale    = workflow["Stale"],
        Started  = workflow["Started"],
    )
    
def _workflow_add_helper(workflow:WorkflowSchema) -> dict:
    d_request = {
        "PFDCMservice"   : workflow.request.PFDCMservice,
        "PACSservice"    : workflow.request.PACSservice,
        "PACSdirective"  : workflow.request.PACSdirective.__dict__,
        "thenArgs"       : workflow.request.thenArgs.__dict__,
        "dblogbasepath"  : workflow.request.dblogbasepath,
        "FeedName"       : workflow.request.FeedName,
        "User"           : workflow.request.User,
        "analysisArgs"   : workflow.request.analysisArgs.__dict__,
    }
    
    return {
        "_id"     : workflow.key,
        "request" : d_request,
        "status"  : workflow.status.__dict__,
        "Stale"   : workflow.Stale,
        "Started" : workflow.Started,
    }
    
def dict_to_query(request:dict)-> DicomStatusQuerySchema:
    return DicomStatusQuerySchema(
        PFDCMservice   = request["PFDCMservice"],
        PACSservice    = request["PACSservice"],
        PACSdirective  = request["PACSdirective"],
        thenArgs       = request["thenArgs"],
        dblogbasepath  = request["dblogbasepath"],
        FeedName       = request["FeedName"],
        User           = request["User"],
        analysisArgs   = request["analysisArgs"],
    )

def query_to_dict(request:DicomStatusQuerySchema)-> dict:
    return {
        "PFDCMservice"   : request.PFDCMservice,
        "PACSservice"    : request.PACSservice,
        "PACSdirective"  : request.PACSdirective.__dict__,
        "thenArgs"       : request.thenArgs.__dict__,
        "dblogbasepath"  : request.dblogbasepath,
        "FeedName"       : request.FeedName,
        "User"           : request.User,
        "analysisArgs"   : request.analysisArgs.__dict__,
    }
    
def dict_to_hash(data:dict) -> str:
    # convert to string and encode
    str_data = json.dumps(data)
    hash_request = hashlib.md5(str_data.encode())     
    # create an unique key
    key = hash_request.hexdigest()
    return key



# DB queries

                   
def update_workflow(key:str, data:dict):
    """
    Update an existing workflow in the DB
    """
    workflow = workflow_collection.find_one({"_id":key})
    if workflow:
        updated_workflow = workflow_collection.update_one(
            {"_id":key},{"$set":_workflow_add_helper(data)}
        )
        if updated_workflow:
            return True
        return False  
        
def retrieve_workflow(key:str) -> dict:
    """
    Retrieve a single workflow from DB
    Given: key
    """
    workflow = workflow_collection.find_one({"_id":key})
    if workflow:
        return _workflow_retrieve_helper(workflow)  
