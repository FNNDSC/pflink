import motor.motor_asyncio
from bson.objectid import ObjectId
import json
import hashlib
import threading
from fastapi import BackgroundTasks
import asyncio
import time
MONGO_DETAILS = "mongodb://localhost:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.workflows

workflow_collection = database.get_collection("workflows_collection")


from models.fnf import (
    FnfSchema,
    FnfResponseSchema,
    FnfWorkflowSchema,
)

# helpers


def workflow_helper(workflow) -> dict:
    return {
        "key": workflow["key"],
        "request": workflow["request"],
        "response": workflow["response"],
    }

def json_to_hash(payload:dict)-> str:
    # stringify json body
    #str_request = json.dumps(payload, separators=(',', ':'))
    str_request = "almond"
    # create a hash for this string
    hash_request = hashlib.md5(str_request.encode()) 
    return hash_request.hexdigest()
    
async def update_status(hash_request,workflow:FnfWorkflowSchema):
    if workflow["response"]["stale"]:
        workflow["response"]["stale"]=False
        await update_workflow(hash_request,workflow)
        print("here")
        asyncio.sleep(4) # equivalent to get a real status and update 
        workflow["response"]["stale"]=True
        await update_workflow(hash_request,workflow)


    
# Add new workflow in the DB
async def add_workflow(workflow_data:dict) -> dict:
    workflow = await workflow_collection.insert_one(workflow_data)
    new_workflow = await workflow_collection.find_one({"_id":workflow.inserted_id})
    return workflow_helper(new_workflow)
    
# Retrieve an existing workflow from DB
async def retrieve_workflow(key:str) -> dict:
    workflow = await workflow_collection.find_one({"key":key})
    if workflow:
        return workflow_helper(workflow)

# update workflow
async def update_workflow(key:str, data:dict):
    print("updaeting")
    if len(data)<1:
        return False
    workflow = await workflow_collection.find_one({"key":key})
    if workflow:
        updated_workflow = await workflow_collection.update_one(
            {"key":key},{"$set":data}
        )
        if updated_workflow:
            return True
        return False
        
# Read/write status from DB
async def fnf_status(request:dict):
    print("requesting status")
    hash_request = json_to_hash(request)    
    workflow = await retrieve_workflow(hash_request)
    if not workflow:
        new_workflow = FnfWorkflowSchema(key=hash_request,request=FnfSchema().__dict__,response=FnfResponseSchema().__dict__)
        workflow = await add_workflow(new_workflow)       
    await update_status(hash_request,workflow)
    
    
# Workflow manager
async def fnf_workflow(request:dict):
    print("updating workflow")
    hash_request = json_to_hash(request)    
    workflow = await retrieve_workflow(hash_request)
    if not workflow:        
        return
    if not workflow["response"]["started"]:
        workflow["response"]["started"] = True
        await update_status(hash_request,workflow)
        # wait and finish workflow
        asyncio.sleep(4)


# fire and forget workflow
async def post_workflow(background_tasks: BackgroundTasks, request:dict):
    await fnf_status(request)
    await fnf_workflow(request)
    hash_request = json_to_hash(request)    
    workflow = await retrieve_workflow(hash_request)
    return workflow["response"]
          
        
        
    
    

