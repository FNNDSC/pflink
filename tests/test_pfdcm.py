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
    response = test_app.post("/api/v1/pfdcm/", content=json.dumps(test_request_payload), )

    assert response.status_code == 201
    assert response.json() == test_response_payload


def test_get_pfdcm_list(test_app, monkeypatch):
    response = test_app.get("/api/v1/pfdcm/list")

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_pfdcm(test_app, monkeypatch):
    test_response_payload = {
        "data": {
            '_id': '437b930db84b8079c2dd804a71936b5f',
            "service_name": "something",
            "service_address": "something else"
        },
        "message": "pfdcm data retrieved successfully."
    }
    response = test_app.get("/api/v1/pfdcm/something")

    assert response.status_code == 200
    assert response.json() == test_response_payload


def test_get_pfdcm_hello(test_app, monkeypatch):
    test_response_payload = {
            "detail": "Unable to reach something else."
        }
    response = test_app.get("/api/v1/pfdcm/something/hello")
    assert response.status_code == 404
    assert response.json() == test_response_payload


def test_get_pfdcm_about(test_app, monkeypatch):
    test_response_payload = {
        "detail": "Unable to reach something else."
    }
    response = test_app.get("/api/v1/pfdcm/something/about")
    assert response.status_code == 404
    assert response.json() == test_response_payload


def test_get_pfdcm_cube_list(test_app, monkeypatch):
    test_response_payload = {
        "detail": "Unable to reach endpoints of something"
    }
    response = test_app.get("/api/v1/pfdcm/something/cube/list")
    assert response.status_code == 404
    assert response.json() == test_response_payload


def test_get_pfdcm_swift_list(test_app, monkeypatch):
    test_response_payload = {
        "detail": "Unable to reach endpoints of something"
    }
    response = test_app.get("/api/v1/pfdcm/something/swift/list")
    assert response.status_code == 404
    assert response.json() == test_response_payload


def test_get_pfdcm_pacs_list(test_app, monkeypatch):
    test_response_payload = {
        "detail": "Unable to reach endpoints of something"
    }
    response = test_app.get("/api/v1/pfdcm/something/PACSservice/list")
    assert response.status_code == 404
    assert response.json() == test_response_payload

# Functional testing


def test_delete_pfdcm(test_app):
    test_response_payload = {
        "Message": "1 record(s) deleted!"
    }
    response = app.controllers.pfdcm.delete_pfdcm("something")
    assert response == test_response_payload
