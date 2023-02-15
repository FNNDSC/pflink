import motor.motor_asyncio
import json
import hashlib
import logging
import subprocess

from models.workflow import (
    State,
    DicomStatusResponseSchema,
    DicomStatusQuerySchema,
    WorkflowSchema,
)

from controllers.pfdcm import (
    retrieve_pfdcm,
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
                   thenArgs      = workflow["request"]["thenArgs"],
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
        "thenArgs"       : workflow.request.thenArgs.__dict__,
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
        "thenArgs"       : request.thenArgs.__dict__,
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
    new_workflow= await workflow_collection.insert_one(workflow_add_helper(workflow_data))
    workflow = await workflow_collection.find_one({"_id":new_workflow.inserted_id})
    return workflow_retrieve_helper(workflow)


    
# Retrieve an existing workflow from DB
async def retrieve_workflow(key:str) -> dict:
    workflow = await workflow_collection.find_one({"_id":key})
    if workflow:
        return workflow_retrieve_helper(workflow)

# Get PFDCM URL
async def retrieve_pfdcm_url(
    serviceName : str,
) -> str:
    """
    Retrieve service address of a PFDCM
    server from the DB
    Given: serviceName
    """
    pfdcm_server = await retrieve_pfdcm(serviceName)    
    pfdcm_url = pfdcm_server['server_ip'] + ":" + pfdcm_server['server_port']
    return pfdcm_url
     
# POST a workflow
async def post_workflow(
    data : DicomStatusQuerySchema
) -> DicomStatusResponseSchema:
    """
    Create a new workflow object and
    store it in DB or retrieve if already
    present.
    Start a new subprocess to create a workflow
    Start a new subprocess to update the database
    """
    d_data = query_to_dict(data)
    str_data = json.dumps(d_data)  
    key = dict_to_hash(d_data)
    
    workflow = await retrieve_workflow(key)
    if not workflow:
        status = DicomStatusResponseSchema()    
        new_workflow = WorkflowSchema(
                       key=key, 
                       request = data, 
                       status=status
                      )
        workflow = await add_workflow(new_workflow)
        
    pfdcm_url = await retrieve_pfdcm_url(data.PFDCMservice)
    status_update = subprocess.Popen(
                               ['python',
                               'app/processes/status.py',
                               "--data",str_data,
                               "--url",pfdcm_url,
                               ], stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               close_fds   = True)
                               
    manage_workflow = subprocess.Popen(
                                ['python',
                                'app/processes/wf_manager.py',
                                "--data",str_data,
                                "--url",pfdcm_url,
                                ], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 close_fds   = True)
    return workflow.status
