import pytest
from app.controllers.subprocesses.status import StatusManager
from app.models.workflow import WorkflowDBSchema, WorkflowStatusResponseSchema, WorkflowRequestSchema, State
from app.controllers.subprocesses import status
import requests

# specify all the fixtures(reusable components) here


@pytest.fixture
def sample_status_manager():
    return StatusManager("args")

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
def test_update_workflow_progress(sample_status_manager):
    test_response = WorkflowStatusResponseSchema()
    resp = sample_status_manager.update_workflow_progress(test_response)
    assert resp.workflow_progress_perc == 0

@pytest.mark.mocktest
def test_get_pfdcm_status(sample_status_manager, sample_request, monkeypatch):
    expected_error = 'PFDCM server is unavailable.'
    def mock_retrieve_pfdcm_url(example):
        return "http://fake_path"

    def mock_post(example,json,headers):
        return {"response":"OK"}

    monkeypatch.setattr(status,"retrieve_pfdcm_url",mock_retrieve_pfdcm_url)
    monkeypatch.setattr(requests,"post",mock_post)
    resp = sample_status_manager.get_pfdcm_status(sample_request)
    assert resp.get('error')
    assert resp['error'].__contains__(expected_error)


@pytest.mark.mocktest
def test_get_simulated_status(sample_status_manager, sample_request):
    test_workflow_record = WorkflowDBSchema(request=sample_request,
                                            response=WorkflowStatusResponseSchema())
    response = sample_status_manager.get_simulated_status(test_workflow_record)
    assert response.workflow_state == State.REGISTERING