import motor.motor_asyncio
import json
import hashlib
import logging
import asyncio
import time

from models.workflow import (
    State,
    DicomStatusResponseSchema,
    DicomStatusQuerySchema,
    WorkflowSchema,
)


MONGO_DETAILS = "mongodb://localhost:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.workflows

workflow_collection = database.get_collection("workflows_collection")

format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=format, 
    level=logging.INFO,
    datefmt="%H:%M:%S"
)

# helpers


def workflow_retrieve_helper(workflow:dict) -> WorkflowSchema:    
    request =  DicomStatusQuerySchema(
                   PFDCMservice  = workflow["request"]["PFDCMservice"],
                   PACSservice   = workflow["request"]["PACSservice"],
                   PACSdirective = workflow["request"]["PACSdirective"],
                   dblogbasepath = workflow["request"]["dblogbasepath"],
                   FeedName      = workflow["request"]["FeedName"],
                   User          = workflow["request"]["User"],
               )
    return WorkflowSchema(
        key      = workflow["_id"],
        request  = request,
        status   = workflow["status"],
    )
    
def workflow_add_helper(workflow:WorkflowSchema) -> dict:
    d_request = {
        "PFDCMservice"   : workflow.request.PFDCMservice,
        "PACSservice"    : workflow.request.PACSservice,
        "PACSdirective"  : workflow.request.PACSdirective.__dict__,
        "dblogbasepath"  : workflow.request.dblogbasepath,
        "FeedName"       : workflow.request.FeedName,
        "User"           : workflow.request.User,
    }
    
    return {
        "_id"     : workflow.key,
        "request" : d_request,
        "status"  : workflow.status.__dict__,
    }
    
def query_to_dict(request:DicomStatusQuerySchema)-> dict:
    return {
        "PFDCMservice"   : request.PFDCMservice,
        "PACSservice"    : request.PACSservice,
        "PACSdirective"  : request.PACSdirective.__dict__,
        "dblogbasepath"  : request.dblogbasepath,
        "FeedName"       : request.FeedName,
        "User"           : request.User,
    }
    

    
def dict_to_hash(data:dict) -> str:
    # convert to string and encode
    str_data = json.dumps(data)
    hash_request = hashlib.md5(str_data.encode()) 
    
    # create an unique key
    key = hash_request.hexdigest()
    return key


# Retrieve all workflows present in the DB
async def retrieve_workflows():
    workflows = []
    async for workflow in workflow_collection.find():
        workflows.append(workflow_retrieve_helper(workflow))
    return workflows
    
        
# Add new workflow in the DB
async def add_workflow(workflow_data:WorkflowSchema) -> dict:
    # check if key already exists
    workflow = await workflow_collection.find_one({"_id":workflow_data.key})
    if not workflow:
        new_workflow= await workflow_collection.insert_one(workflow_add_helper(workflow_data))
        workflow = await workflow_collection.find_one({"_id":new_workflow.inserted_id})
    return workflow_retrieve_helper(workflow)


    
# Retrieve an existing workflow from DB
async def retrieve_workflow(key:str) -> dict:
    workflow = await workflow_collection.find_one({"_id":key})
    if workflow:
        return workflow_retrieve_helper(workflow)
        
# POST a workflow
async def post_workflow(data:DicomStatusQuerySchema)->DicomStatusResponseSchema:    
    key = dict_to_hash(query_to_dict(data))
    status = DicomStatusResponseSchema()    
    new_workflow = WorkflowSchema(key=key, request = data, status=status)
    added_workflow = await add_workflow(new_workflow)
        
    return {
        "key"     : key,
        "status": added_workflow.status,
        }
