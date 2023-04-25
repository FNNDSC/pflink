import json
import app
import httpx


def test_create_workflow(test_app, monkeypatch):
    test_request_payload = {
        "pfdcm_info": {
            "pfdcm_service": "PFDCM",
            "PACS_service": "orthanc"
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
    response = test_app.post("api/v1/workflow/", content=json.dumps(test_request_payload))

    assert response.json() == test_response_payload


def test_get_all_workflows(test_app, monkeypatch):
    response = test_app.get("/api/v1/testing/list")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_delete_workflow(test_app):
    test_request_payload = {
      "pfdcm_info": {
        "pfdcm_service": "PFDCM",
        "PACS_service": "orthanc",
        "cube_service": "local",
        "swift_service": "local",
        "dicom_file_extension": "dcm",
        "db_log_path": "/home/dicom/log"
      },
      "PACS_directive": {
        "AccessionNumber": "",
        "PatientID": "",
        "PatientName": "",
        "PatientBirthDate": "",
        "PatientAge": "",
        "PatientSex": "",
        "StudyDate": "",
        "StudyDescription": "",
        "StudyInstanceUID": "12365548",
        "Modality": "",
        "ModalitiesInStudy": "",
        "PerformedStationAETitle": "",
        "NumberOfSeriesRelatedInstances": "",
        "InstanceNumber": "",
        "SeriesDate": "",
        "SeriesDescription": "",
        "SeriesInstanceUID": "66412098598",
        "ProtocolName": "",
        "AcquisitionProtocolDescription": "",
        "AcquisitionProtocolName": ""
      },
      "workflow_info": {
        "feed_name": "test-%SeriesInstanceUID",
        "user_name": "clinical_user",
        "plugin_name": "pl-dircopy",
        "plugin_version": "1.1.0",
        "plugin_params": "--args ARGS",
        "pipeline_name": ""
      }
    }
    test_response_payload = {
        "Message": "1 record(s) deleted!"
    }
    response = app.controllers.workflow.delete_workflow(test_request_payload)

    assert response == test_response_payload
