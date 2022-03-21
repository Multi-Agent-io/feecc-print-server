import pytest
from app import app
from fastapi.testclient import TestClient

test_client = TestClient(app)


@pytest.fixture
def test_img() -> str:
    return "robonomics.jpg"


@pytest.mark.printer
def test_print_image(test_img) -> None:
    resp = test_client.post("/print_image", files={"image_file": open(test_img, "rb")})
    assert resp.ok
    assert resp.json().get("status") == 200


@pytest.mark.printer
def test_print_image_annotated(test_img) -> None:
    resp = test_client.post(
        "/print_image",
        files={"image_file": open(test_img, "rb")},
        data={"annotation": "image with annotation"},
    )
    assert resp.ok
    assert resp.json().get("status") == 200
