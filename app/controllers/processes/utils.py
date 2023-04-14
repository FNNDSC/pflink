import hashlib
import json

from pymongo import MongoClient

from config import settings
from workflow import (
    WorkflowRequestSchema,
    WorkflowDBSchema,
)

MONGO_DETAILS = str(settings.pflink_mongodb)

client = MongoClient(MONGO_DETAILS)

database = client.workflows

workflow_collection = database.get_collection("workflows_collection")



# helpers


def _workflow_retrieve_helper(workflow:dict) -> WorkflowDBSchema:
    request =  WorkflowRequestSchema(
                   pfdcm_info=workflow["request"]["pfdcm_info"],
                   pacs_directive=workflow["request"]["pacs_directive"],
                   workflow_info=workflow["request"]["workflow_info"],
               )
    return WorkflowDBSchema(
        key=workflow["_id"],
        request=request,
        response=workflow["response"],
        stale=workflow["stale"],
        started=workflow["started"],
    )


def _workflow_add_helper(workflow: WorkflowDBSchema) -> dict:
    d_request = {
        "pfdcm_info": workflow.request.pfdcm_info.__dict__,
        "pacs_directive": workflow.request.pacs_directive.__dict__,
        "workflow_info": workflow.request.workflow_info.__dict__,
    }
    
    return {
        "_id": workflow.key,
        "request": d_request,
        "response": workflow.response.__dict__,
        "stale": workflow.stale,
        "started": workflow.started,
    }


def dict_to_query(request: dict) -> WorkflowRequestSchema:
    return WorkflowRequestSchema(
        pfdcm_info=request["pfdcm_info"],
        pacs_directive=request["pacs_directive"],
        workflow_info=request["workflow_info"],
    )


def query_to_dict(request: WorkflowRequestSchema) -> dict:
    return {
        "pfdcm_info": request.pfdcm_info.__dict__,
        "pacs_directive": request.pacs_directive.__dict__,
        "workflow_info": request.workflow_info.__dict__,
    }


def dict_to_hash(data:dict) -> str:
    # convert to string and encode
    str_data = json.dumps(data)
    hash_request = hashlib.md5(str_data.encode())     
    # create a unique key
    key = hash_request.hexdigest()
    return key

# DB queries

                   
def update_workflow(key: str, data: WorkflowDBSchema) -> bool:
    """
    Update an existing workflow in the DB
    """
    workflow = workflow_collection.find_one({"_id":key})
    if workflow:
        updated_workflow = workflow_collection.update_one(
            {"_id": key}, {"$set": _workflow_add_helper(data)}
        )
        if updated_workflow:
            return True
        return False  


async def retrieve_pfdcm_url(service_name: str) -> str:
    pfdcm_server = await retrieve_pfdcm(service_name)
    if not pfdcm_server:
        raise Exception(f"Service {service_name} not found in the DB")

    pfdcm_url = pfdcm_server['server_ip'] + ":" + pfdcm_server['server_port']
    return pfdcm_url


def retrieve_workflow(key: str) -> WorkflowDBSchema:
    """
    Retrieve a single workflow from DB
    Given: key
    """
    workflow = workflow_collection.find_one({"_id": key})
    if workflow:
        return _workflow_retrieve_helper(workflow)  
