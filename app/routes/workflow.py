from fastapi import APIRouter, Body
import  subprocess
import json

from models.workflow import (
    DicomStatusQuerySchema,
    DicomActionQuerySchema,
    PACSqueyReturnModel,
    DicomStatusResponseSchema,
)
from controllers.workflow import (
    post_workflow,
    retrieve_workflows,
    query_to_dict,
)

from controllers.pfdcm import (
    retrieve_pfdcm,
)

router = APIRouter()
    
@router.get("/",response_description="All workflows retrieved")
async def get_workflows():
    workflows = await retrieve_workflows()
    return workflows
    
@router.post("/",response_description="POST new workflow request")
async def create_workflow(data:DicomStatusQuerySchema) ->DicomStatusResponseSchema:
    d_data = query_to_dict(data)
    str_data = json.dumps(d_data)
    pfdcm_name = data.PFDCMservice
    pfdcm_server = await retrieve_pfdcm(pfdcm_name)    
    pfdcm_url = pfdcm_server['server_ip'] + ":" +pfdcm_server['server_port']
    response = await post_workflow(data)   
    process = subprocess.Popen(['python','app/processes/status.py',"--data",str_data,"--url",pfdcm_url,"--key",response["key"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds   = True)
    process2 = subprocess.Popen(['python','app/processes/wf_manager.py',"--data",str_data,"--url",pfdcm_url,"--key",response["key"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds   = True)
    #stdout,stderr=process2.communicate(b'\n')
    #print(stdout,stderr)
    return response["status"]
