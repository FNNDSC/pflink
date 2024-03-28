import pytest
from app.controllers.subprocesses.wf_manager import WorkflowManager
from app.models.workflow import WorkflowDBSchema, WorkflowStatusResponseSchema, WorkflowRequestSchema, State
from app.controllers.subprocesses import status
import requests

# specify all the fixtures(reusable components) here
@pytest.fixture
def sample_workflow_manager():
    return WorkflowManager("args")

@pytest.fixture
def sample_request(sample_workflow_request):
    return WorkflowRequestSchema(pfdcm_info=sample_workflow_request["pfdcm_info"],
                                 PACS_directive=sample_workflow_request["PACS_directive"],
                                 workflow_info=sample_workflow_request["workflow_info"],
                                 cube_user_info=sample_workflow_request["cube_user_info"])


"""
Your test cases go here
"""
@pytest.mark.mocktest
def test_str_to_param_dict(sample_workflow_manager):
    test_CLI_args = "--some param --boolParam --others ott"
    exp_result = {"some": "param","boolParam": True, "others": "ott"}
    act_result = sample_workflow_manager.str_to_param_dict(test_CLI_args)
    assert exp_result == act_result

@pytest.mark.mocktest
def test_shorten(sample_workflow_manager):
    test_string = "My super long long string"
    test_max_char = 10
    act_result = sample_workflow_manager.shorten(test_string,test_max_char)
    assert len(act_result) == 10

@pytest.mark.mocktest
def test_is_retry_valid(sample_workflow_manager, sample_workflow_request):
    test_workflow = WorkflowDBSchema(request=sample_workflow_request,
                                     response=WorkflowStatusResponseSchema())
    test_workflow.service_retry = 6
    result = sample_workflow_manager.is_retry_valid(test_workflow)
    assert result == False

