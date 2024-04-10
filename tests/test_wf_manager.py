import pytest
from app.controllers.subprocesses.wf_manager import WorkflowManager, shorten, str_to_param_dict
from app.controllers.subprocesses import wf_manager, utils
from app.models.workflow import WorkflowDBSchema, WorkflowStatusResponseSchema, WorkflowRequestSchema, State

# specify all the fixtures(reusable components) here
@pytest.fixture
def sample_workflow_manager(monkeypatch, sample_workflow_entry):
    workflow_manager = WorkflowManager("args")
    def mock_retrieve_workflow(db_key, test):
        return utils.workflow_retrieve_helper(sample_workflow_entry)

    def mock_retrieve_pfdcm_url(service_name):
        return "http://random_url"

    def mock_get_cube_url_from_pfdcm(url, service):
        return "http://fake_cube"

    def mock_do_cube_create_user(url, uname, pwd):
        return None

    monkeypatch.setattr(wf_manager, "retrieve_pfdcm_url", mock_retrieve_pfdcm_url)
    monkeypatch.setattr(wf_manager, "retrieve_workflow", mock_retrieve_workflow)
    monkeypatch.setattr(wf_manager, "get_cube_url_from_pfdcm", mock_get_cube_url_from_pfdcm)
    monkeypatch.setattr(wf_manager, "do_cube_create_user", mock_do_cube_create_user)
    workflow_manager.fetch_and_load("",True)
    return workflow_manager


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
    act_result = str_to_param_dict(test_CLI_args)
    assert exp_result == act_result

@pytest.mark.mocktest
def test_shorten(sample_workflow_manager):
    test_string = "My super long long string"
    test_max_char = 10
    act_result = shorten(test_string,test_max_char)
    assert len(act_result) == 10

@pytest.mark.mocktest
def test_analysis_retry(sample_workflow_manager):
    retry_possible = sample_workflow_manager.analysis_retry("key")
    assert retry_possible == False

@pytest.mark.mocktest
def test_is_retry_valid(sample_workflow_manager):
    result = sample_workflow_manager.is_retry_valid()
    assert result == False

