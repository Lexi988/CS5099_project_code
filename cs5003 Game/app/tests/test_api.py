#/app/tests/test_api.pu
import pytest
from app.controller.server_controller import create_app 
# Remove the problematic import
# import app.view.login_view as login_view

"""
#REF:

pytest logic/code and fixtures for testing adapted from:

https://docs.pytest.org/en/stable/
https://docs.pytest.org/en/stable/reference/fixtures.html#fixture
https://realpython.com/python-testing/#pytest
https://realpython.com/pytest-python-testing/
https://flask.palletsprojects.com/en/stable/patterns/appfactories/
https://www.youtube.com/watch?v=EgpLj86ZHFQ 'Please Learn How To Write Tests in Python… • Pytest Tutorial' by Tech with Tim
"""

@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()

def test_login_unknown_user(client):
    rv = client.post("/login", json={"username":"ghost","password":"x"})
    assert rv.status_code == 401