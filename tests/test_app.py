import copy

test_app_description = """
Tests for the FastAPI backend defined in src/app.py.

These exercises exercise the public API using the TestClient and ensure the
in-memory activity store is reset between tests so that each one runs with a
predictable starting state.
"""

from fastapi.testclient import TestClient

from src.app import app, activities


import pytest


@pytest.fixture
def client():
    """Create a TestClient for the application."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the global `activities` dictionary before each test.

    The backend stores data in a mutable global variable; without resetting,
    tests would interfere with one another.  This fixture captures a deep copy
    and restores it after the test completes.
    """
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


# ---- functional tests ------------------------------------------------------

def test_root_redirect(client):
    # Arrange/Act: request the root path
    response = client.get("/")

    # Assert: should redirect to our static index page
    assert response.status_code == 200
    # Response history should show a redirect followed by successful content
    assert str(response.url).endswith("/static/index.html")


def test_get_activities(client):
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # some activity names should appear
    assert "Chess Club" in data


def test_signup_success(client):
    email = "newstudent@mergington.edu"
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    assert response.status_code == 200
    assert email in activities["Chess Club"]["participants"]


def test_signup_duplicate(client):
    existing = activities["Chess Club"]["participants"][0]
    response = client.post(
        "/activities/Chess Club/signup", params={"email": existing}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_remove_participant_success(client):
    student = activities["Chess Club"]["participants"][0]
    response = client.delete(
        "/activities/Chess Club/participants", params={"email": student}
    )
    assert response.status_code == 200
    assert student not in activities["Chess Club"]["participants"]


def test_remove_nonexistent_participant(client):
    response = client.delete(
        "/activities/Chess Club/participants", params={"email": "nobody@mergington.edu"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_remove_from_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/participants", params={"email": "x@x.com"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
