import json
import pytest
import sys
import app


def test_create_pfdcm(test_app, monkeypatch):
    test_request_payload = {"service_name": "something", "service_address": "something else"}
    test_response_payload = {'data': {},'message': 'service_name must be unique. something already exists.'}

    async def mock_post(payload):
        return 1

    monkeypatch.setattr(app.controllers.pfdcm,"add_pfdcm", mock_post)
    response = test_app.post("/pfdcm/", content=json.dumps(test_request_payload),)
    
    assert response.status_code == 200
    assert response.json() == test_response_payload
