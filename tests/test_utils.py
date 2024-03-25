import pytest
import json
from app.controllers.subprocesses.utils import (
    str_to_hash,
    dict_to_query,
    query_to_dict,
    substitute_dicom_tags,
    workflow_retrieve_helper,
    workflow_add_helper,
)


@pytest.mark.unittest
def test_str_to_hash():
    test_string = "apple"
    test_hash = "1f3870be274f6c49b3e31a0c6728957f"
    assert str_to_hash(test_string) == test_hash


@pytest.mark.unittest
def test_serialization_and_deserialization(sample_workflow_request):
    # del sample_workflow_request['cube_user_info']
    d_request = json.dumps(sample_workflow_request)
    assert query_to_dict(dict_to_query(sample_workflow_request)) == d_request


@pytest.mark.unittest
def test_substitute_dicom_tags():
    test_d_dicom = {"PatientID": "1237", "PatientAge": "27"}
    test_name = "testing-%PatientID-%PatientAge"
    test_result = "testing-1237-27"
    assert substitute_dicom_tags(test_name, test_d_dicom) == test_result


@pytest.mark.unittest
def test_workflow_add_and_retrieve_helper(sample_workflow_entry):
    assert workflow_add_helper(workflow_retrieve_helper(sample_workflow_entry)) == sample_workflow_entry

