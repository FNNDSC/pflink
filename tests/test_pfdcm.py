import json
import app


def test_create_pfdcm(test_app, monkeypatch):
    test_request_payload = {"service_name": "something", "service_address": "something else"}
    test_response_payload = {
        'data': {
            '_id': '437b930db84b8079c2dd804a71936b5f',
            'service_address': 'something else',
            'service_name': 'something'
        },
        'message': 'New record created.'
    }

    async def mock_post(payload):
        return 1

    monkeypatch.setattr(app.controllers.pfdcm, "add_pfdcm", mock_post)
    response = test_app.post("/pfdcm/", content=json.dumps(test_request_payload), )

    assert response.status_code == 200
    assert response.json() == test_response_payload


def test_get_pfdcms(test_app, monkeypatch):
    response = test_app.get("/pfdcm/")

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_pfdcm(test_app, monkeypatch):
    test_response_payload = {
        "data": {
            "_id": "437b930db84b8079c2dd804a71936b5f",
            "service_name": "something",
            "service_address": "something else"
        },
        "message": "pfdcm data retrieved successfully."
    }
    response = test_app.get("/pfdcm/something")

    assert response.status_code == 200
    assert response.json() == test_response_payload


def test_get_pfdcm_hello(test_app, monkeypatch):
    test_response_payload = {
        "data": {
            "error": "something else/api/v1/hello/ does not exist."
        },
        "message": ""
    }
    response = test_app.get("/pfdcm/something/hello")
    assert response.status_code == 200
    assert response.json() == test_response_payload


def test_get_pfdcm_about(test_app, monkeypatch):
    test_response_payload = {
        "data": {
            "error": "something else/api/v1/about/ does not exist."
        },
        "message": ""
    }
    response = test_app.get("/pfdcm/something/about")
    assert response.status_code == 200
    assert response.json() == test_response_payload
