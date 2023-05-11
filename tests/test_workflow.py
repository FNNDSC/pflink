import json
import app
import pytest
from app.controllers.subprocesses import utils
from app.controllers import workflow


@pytest.mark.mocktest
def test_create_workflow(test_app, monkeypatch, sample_workflow_request, sample_workflow_entry, auth_token):
    def mock_retrieve_workflow(key):
        return utils.workflow_retrieve_helper(sample_workflow_entry)

    monkeypatch.setattr(utils, "retrieve_workflow", mock_retrieve_workflow)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.post("api/v1/workflow", data=json.dumps(sample_workflow_request), headers=headers)
    assert response.status_code == 200
    assert response.json() == sample_workflow_entry["response"]


@pytest.mark.mocktest
def test_get_all_workflows(test_app, monkeypatch, sample_workflow_entry, auth_token):
    def mock_retrieve_workflows():
        return [utils.workflow_retrieve_helper(sample_workflow_entry)]
    monkeypatch.setattr(workflow, "retrieve_workflows", mock_retrieve_workflows)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/testing/list", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
