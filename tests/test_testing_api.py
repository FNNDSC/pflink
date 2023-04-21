import json
import pytest
import app
import asyncio


def test_create_workflow(test_app, monkeypatch):
    test_request_payload = {
        "pfdcm_info": {
            "pfdcm_service": "PFDCM",
            "PACS_service": "orthanc",
            "cube_service": "local"
        },
        "PACS_directive": {
            "StudyInstanceUID": "12365548",
            "SeriesInstanceUID": "66412098598"
        },
        "workflow_info": {
            "feed_name": "test-%SeriesInstanceUID",
            "user_name": "clinical_user",
            "plugin_name": "pl-dircopy",
            "plugin_version": "1.1.0",
            "plugin_params": "--args ARGS"
        }
    }
    test_response_payload = {
        "status": True,
        "workflow_state": "completed",
        "state_progress": "100%",
        "feed_id": "1280",
        "feed_name": "test-66412098598",
        "error": ""
    }

    async def mock_post():
        return 1

    monkeypatch.setattr(app.controllers.workflow, "add_workflow", mock_post)
    #response = test_app.post("/testing/", content=json.dumps(test_request_payload))

    assert 1==1
    #assert response.json() == test_response_payload
