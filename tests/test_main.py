from app.config import settings
def test_root(test_app):
    response = test_app.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to pflink app!"}
  
    
def test_hello(test_app):
    response = test_app.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello! from pflink"}
 
    
def test_about(test_app):
    response = test_app.get("/about")
    assert response.status_code == 200
    assert response.json() =={'about': 'App to communicate with pfdcm and CUBE', 'name': 'pflink', 'version': f'{settings.version}'}

