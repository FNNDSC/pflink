import motor.motor_asyncio
import json
import hashlib
import logging
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from models.fnf import (
    State,
    FnfRequestSchema,
    FnfStatusSchema,
    FnfWorkflowSchema,
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


def workflow_retrieve_helper(workflow:dict) -> FnfWorkflowSchema:
    return FnfWorkflowSchema(
        key      = workflow["_id"],
        request  = workflow["request"],
        status   = workflow["status"],
    )
    
def workflow_add_helper(workflow:FnfWorkflowSchema) -> dict:
    return {
        "_id"     : workflow.key,
        "request" : workflow.request.__dict__,
        "status"  : workflow.status.__dict__,
    }
    
def dict_to_hash(data:dict) -> str:
    # convert to string and encode
    str_data = json.dumps(vars(data))
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
async def add_workflow(workflow_data:FnfWorkflowSchema) -> dict:
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


# update workflow
def update_workflow(key:str, data:FnfRequestSchema):
    workflow = workflow_collection.find_one({"_id":key})
    if workflow:
        updated_workflow = workflow_collection.update_one(
            {"_id":key},{"$set":workflow_add_helper(data)}
        )
        if updated_workflow:
            return True
        return False
        
# POST a workflow
async def post_workflow(data:FnfRequestSchema)->FnfStatusSchema:    
    key = dict_to_hash(data)
    status = FnfStatusSchema()    
    new_workflow = FnfWorkflowSchema(key=key, request = data, status=status)
    added_workflow = await add_workflow(new_workflow)
    
    #shell = jobber({'verbosity' : 1, 'noJobLogging': True})
    #shell.job_runbg('python -c "str_cmd"')
    #shell.job_runbg("python -c 'from controllers.fnf import manage_workflow; manage_workflow(key)'")
    
    
    return {
        "key"     : key,
        "status": added_workflow.status,
        }
        
    
# Update status of a workflow
async def update_status(key:str):
    workflow = await retrieve_workflow(key)    
    loop = asyncio.get_running_loop()
    exe = ProcessPoolExecutor(4)
    awaitable = loop.run_in_executor(exe, blocking_method,key,workflow)
     # await the task
    await awaitable
    # close the process pool
    exe.shutdown()
        
        
# Blocking method 
def blocking_method(key,workflow):
    if workflow.status.stale and not workflow.status.taskState==State.FINISHED.name: 
        logging.info(f"WORKING on updating the status for {key}, locking--")       
        workflow.status.stale=False
        update_workflow(key,workflow)
        time.sleep(20)
        workflow.status.taskProgress += 10
        workflow.status.stale=True    
        update_workflow(key,workflow)
        logging.info(f"UPDATED status for {key}, releasing lock")
    
    
    
# manage a workflow
async def manage_workflow(key:str):
    workflow = await retrieve_workflow(key)
    if not workflow.status.started:
        logging.info(f"STARTED working on workflow {key}")
        workflow.status.started = True
        update_workflow(key,workflow)
        progress = workflow.status.taskProgress
        while progress<100:
            if progress <=30:
                workflow.status.taskState = State.INIT.name
            elif progress >30 and progress <=90:
                workflow.status.taskState = State.PROGRESS.name
            update_workflow(key,workflow)
            await update_status(key)          
            await asyncio.sleep(40)            
            workflow = await retrieve_workflow(key)
            progress = workflow.status.taskProgress
        workflow.status.taskState = State.FINISHED.name
        logging.info(f"FINISHED workflow: {key}")
        update_workflow(key,workflow)


                
        
        
            
        
        
    
