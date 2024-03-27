import pytest
from app.controllers import cube

@pytest.mark.mocktest
def test_get_plugins_not_found(test_app, monkeypatch, auth_token):
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/cube/plugin/list?pfdcm_name=PFDCM&cube_name=local", headers=headers)
    assert response.status_code == 404

@pytest.mark.mocktest
def test_get_plugins_found(test_app, monkeypatch, auth_token):
    async def mock_get_plugins(name, nam):
        return ["pl-dircopy", "pl-simpledsapp"]

    monkeypatch.setattr(cube, "get_plugins", mock_get_plugins)
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_app.get("/api/v1/cube/plugin/list?pfdcm_name=PFDCM&cube_name=local", headers=headers)
    assert response.status_code == 200