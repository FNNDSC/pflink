import json
import app


def test_create_workflow(test_app, monkeypatch):
    test_request_payload = {
        "pfdcm_info": {
            "pfdcm_service": "PFDCM",
            "PACS_service": "orthanc",
            "swift_service_PACS": "orthanc"
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
        "workflow_state": "initializing workflow",
        "state_progress": "0%",
        "feed_id": "",
        "feed_name": "",
        "error": ""
    }

    async def mock_post(payload):
        return 1

    monkeypatch.setattr(app.controllers.workflow, "post_workflow", mock_post)
    response = test_app.post("/workflow/", content=json.dumps(test_request_payload))

    assert response.json() == test_response_payload


def test_get_all_workflows(test_app, monkeypatch):
    response = test_app.get("/testing/")
    assert response.status_code == 200
    assert len(response.json()) == 1

