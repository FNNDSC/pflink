import pytest
from app.controllers import auth

@pytest.mark.mocktest
def test_invalid_auth(test_app,):
    """
    Test case for failed authentication
    """
    test_response = {
        "detail": "Incorrect username"
    }
    data = '&username=bla&password=bla'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = test_app.post("/api/v1/auth-token",headers=headers, data=data)
    assert response.status_code == 401
    assert response.json() == test_response

@pytest.mark.mocktest
def test_valid_auth(test_app):
    """
    Test case for valid authentication
    """
    data = '&username=pflink&password=pflink1234'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = test_app.post("/api/v1/auth-token",headers=headers, data=data)
    assert response.status_code == 200

@pytest.mark.mocktest
def test_incorrect_username(test_app,):
    """
    Test case for incorrect username
    """
    test_response = {
        "detail": "Incorrect username"
    }
    data = '&username=bla&password=pflink1234'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = test_app.post("/api/v1/auth-token",headers=headers, data=data)
    assert response.status_code == 401
    assert response.json() == test_response

@pytest.mark.mocktest
def test_incorrect_password(test_app,):
    """
    Test case for incorrect password
    """
    test_response = {
        "detail": "Incorrect password"
    }
    data = '&username=pflink&password=bla'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = test_app.post("/api/v1/auth-token",headers=headers, data=data)
    assert response.status_code == 401
    assert response.json() == test_response