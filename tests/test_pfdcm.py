import json
import app
import pytest
from app.controllers import pfdcm


@pytest.fixture
def sample_list_response():
    return ["local", "remote"]


@pytest.fixture
def sample_response_payload():
    return {
        'data': {
            '_id': '437b930db84b8079c2dd804a71936b5f',
            'service_address': 'something else',
            'service_name': 'something'
        },
        'message': 'New record created.'
    }


@pytest.mark.mocktest
def test_create_pfdcm(test_app, monkeypatch, sample_response_payload, auth_token):
    test_request_payload = {"service_name": "something", "service_address": "something else"}

    async def mock_add_pfdcm(payload):
        return sample_response_payload['data']

    monkeypatch.setattr(pfdcm, "add_pfdcm", mock_add_pfdcm)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.post("/api/v1/pfdcm", data=json.dumps(test_request_payload), headers=headers)
    assert response.status_code == 201
    assert response.json() == sample_response_payload


@pytest.mark.mocktest
def test_get_pfdcm_list(test_app, monkeypatch, sample_list_response, auth_token):
    async def mock_retrieve_pfdcms():
        return sample_list_response

    monkeypatch.setattr(pfdcm, "retrieve_pfdcms", mock_retrieve_pfdcms)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/pfdcm/list", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.mocktest
def test_get_pfdcm(test_app, monkeypatch, sample_response_payload, auth_token):
    sample_response_payload["message"] = 'pfdcm data retrieved successfully.'

    def mock_retrieve_pfdcm(name) -> dict:
        return sample_response_payload["data"]

    monkeypatch.setattr(pfdcm, "retrieve_pfdcm", mock_retrieve_pfdcm)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/pfdcm/something", headers=headers)
    assert response.status_code == 200
    assert response.json() == sample_response_payload


@pytest.mark.mocktest
def test_get_pfdcm_hello(test_app, monkeypatch, auth_token):
    test_response_payload = {
        "data": {
            "detail": "mocking hello response from pfdcm something"
        },
        "message": ""
    }

    async def mock_hello_pfdcm(name):
        return {"detail": f"mocking hello response from pfdcm {name}"}

    monkeypatch.setattr(pfdcm, "hello_pfdcm", mock_hello_pfdcm)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/pfdcm/something/hello", headers=headers)
    assert response.status_code == 200
    assert response.json() == test_response_payload


@pytest.mark.mocktest
def test_get_pfdcm_about(test_app, monkeypatch, auth_token):
    test_response_payload = {
        "data": {
            "detail": "mocking about response from pfdcm something"
        },
        "message": ""
    }

    async def mock_about_pfdcm(name):
        return {"detail": f"mocking about response from pfdcm {name}"}

    monkeypatch.setattr(pfdcm, "about_pfdcm", mock_about_pfdcm)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/pfdcm/something/about", headers=headers)
    assert response.status_code == 200
    assert response.json() == test_response_payload


@pytest.mark.mocktest
def test_get_pfdcm_cube_list(test_app, monkeypatch, sample_list_response, auth_token):
    async def mock_cube_list(name):
        return sample_list_response

    monkeypatch.setattr(pfdcm, "cube_list", mock_cube_list)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/pfdcm/something/cube/list", headers=headers)
    assert response.status_code == 200
    assert response.json() == sample_list_response


@pytest.mark.mocktest
def test_get_pfdcm_swift_list(test_app, monkeypatch, sample_list_response, auth_token):
    async def mock_swift_list(name):
        return sample_list_response

    monkeypatch.setattr(pfdcm, "storage_list", mock_swift_list)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/pfdcm/something/storage/list", headers=headers)
    assert response.status_code == 200
    assert response.json() == sample_list_response


@pytest.mark.mocktest
def test_get_pfdcm_pacs_list(test_app, monkeypatch, sample_list_response, auth_token):
    async def mock_pacs_list(name):
        return sample_list_response

    monkeypatch.setattr(pfdcm, "pacs_list", mock_pacs_list)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/pfdcm/something/PACSservice/list", headers=headers)
    assert response.status_code == 200
    assert response.json() == sample_list_response
