import pytest
from starlette.testclient import TestClient
from app.controllers.auth import create_access_token
from app.models.workflow import State
from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture
def auth_token():
    return create_access_token("pflink")


@pytest.fixture
def sample_workflow_entry():
    return {
        "_id": "e3bcafc90fd53d82bf409f4c7f3f7a73",
        "fingerprint": "hashedtext",
        "creation_time": "2024-03-25 22:34:10",
        "request": {
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
                "SeriesInstanceUID": "66498598",
                "ProtocolName": "",
                "AcquisitionProtocolDescription": "",
                "AcquisitionProtocolName": ""
            },
            "workflow_info": {
                "feed_name": "test-%SeriesInstanceUID",
                "plugin_name": "pl-dircopy",
                "plugin_version": "1.1.0",
                "plugin_params": "--args ARGS",
                "pipeline_name": ""
            },
            "cube_user_info": {
                "username": "chris",
                "password": "chris1234"
            }
        },
        "response": {
            "status": True,
            "workflow_state":  State.INITIALIZING,
            "state_progress": "0%",
            "feed_id": "",
            "feed_name": "",
            "message": "",
            "duplicates": None,
            "error": "",
            "workflow_progress_perc": 0
        },
        "service_retry": 0,
        "stale": True,
        "started": False,
        "feed_requested": False,
        "feed_id_generated": ""
    }


@pytest.fixture
def sample_workflow_request():
    return {
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
            "SeriesInstanceUID": "66498598",
            "ProtocolName": "",
            "AcquisitionProtocolDescription": "",
            "AcquisitionProtocolName": ""
        },
        "workflow_info": {
            "feed_name": "test-%SeriesInstanceUID",
            "plugin_name": "pl-dircopy",
            "plugin_version": "1.1.0",
            "plugin_params": "--args ARGS",
            "pipeline_name": ""
        },
        "cube_user_info": {
            "username": "chris",
            "password": "chris1234"
        }
    }
