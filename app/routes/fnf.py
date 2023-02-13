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
    str_cmd = "from app.controllers.test_file import foo,bar; foo()"
    process = subprocess.Popen(['python','-c',str_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds   = True)
    #stdout,stderr=process.communicate(b'\n')
    #print(stdout,stderr)
    return response["status"]
    
        
# a test blocking method
def blocking_test(message):
    for i in range(0,5):
        print(message)
        time.sleep(2)

