import pytest
from starlette.testclient import TestClient
import asyncio
from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture
def sample_workflow_entry():
    return {
        "_id": "e3bcafc90fd53d82bf409f4c7f3f7a73",
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
                "user_name": "clinical_user",
                "plugin_name": "pl-dircopy",
                "plugin_version": "1.1.0",
                "plugin_params": "--args ARGS",
                "pipeline_name": ""
            }
        },
        "response": {
            "status": True,
            "workflow_state": "initializing workflow",
            "state_progress": "0%",
            "feed_id": "",
            "feed_name": "",
            "error": ""
        },
        "stale": True,
        "started": False
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
                "user_name": "clinical_user",
                "plugin_name": "pl-dircopy",
                "plugin_version": "1.1.0",
                "plugin_params": "--args ARGS",
                "pipeline_name": ""
            }
        }
