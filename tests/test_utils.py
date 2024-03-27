import pytest
import json
from app.controllers.subprocesses.utils import (
    str_to_hash,
    dict_to_query,
    query_to_dict,
    substitute_dicom_tags,
    workflow_retrieve_helper,
    workflow_add_helper,
    do_cube_create_user,
)
import requests
from app.controllers.subprocesses.python_chris_client import PythonChrisClient


@pytest.mark.unittest
def test_str_to_hash():
    test_string = "apple"
    test_hash = "1f3870be274f6c49b3e31a0c6728957f"
    assert str_to_hash(test_string) == test_hash


@pytest.mark.unittest
def test_substitute_dicom_tags():
    test_d_dicom = {"PatientID": "1237", "PatientAge": "27"}
    test_name = "testing-%PatientID-%PatientAge"
    test_result = "testing-1237-27"
    assert substitute_dicom_tags(test_name, test_d_dicom) == test_result


@pytest.mark.unittest
def test_workflow_add_and_retrieve_helper(sample_workflow_entry):
    assert workflow_add_helper(workflow_retrieve_helper(sample_workflow_entry)) == sample_workflow_entry


@pytest.mark.unittest
def test_do_cube_create_user(monkeypatch):
    test_username: str = "cube"
    test_password: str = "password"
    test_url: str = "http://localhost:8000/api/v1"
    def mock_create_user(url,json,headers):
        return {}
    monkeypatch.setattr(requests,"post", mock_create_user)
    response = do_cube_create_user(test_url, test_username, test_password)
    assert type(response) == type(PythonChrisClient(test_url, test_username, test_password))

