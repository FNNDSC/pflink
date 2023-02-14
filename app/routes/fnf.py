from fastapi import APIRouter, Body, BackgroundTasks
import asyncio
import  subprocess
import time
from controllers.fnf import (
    update_status,
    post_workflow,
    manage_workflow,
    retrieve_workflows,
)

from models.fnf import (
    FnfRequestSchema,
    FnfStatusSchema,
)

router = APIRouter()

@router.get("/",response_description="All workflows retrieved")
async def get_workflows():
    workflows = await retrieve_workflows()
    return workflows
    
@router.post("/",response_description="POST new workflow request")
async def create_workflow(background_tasks:BackgroundTasks, data:FnfRequestSchema) ->FnfStatusSchema:
    response = await post_workflow(data)
    #background_tasks.add_task(update_status,response["key"])
    #background_tasks.add_task(manage_workflow,response["key"])
    process1 = subprocess.Popen(['python','app/processes/test_file.py',"--argument",response["key"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds   = True)
    stdout,stderr=process1.communicate(b'\n')
    print(stdout,stderr)
    process2 = subprocess.Popen(['python','app/processes/test_file_2.py',"--argument",response["key"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds   = True)
    
    return response["status"]
    

