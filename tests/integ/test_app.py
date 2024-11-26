import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from unittest.mock import MagicMock
from src.app import app

client = TestClient(app)


@pytest.mark.integration
def test_analyze_video_endpoint(mocker):
    # Mock cv2.VideoCapture behavior
    mock_video_capture = mocker.patch("cv2.VideoCapture")
    mock_cap = MagicMock()
    mock_cap.isOpened.side_effect = [True, False]  # Only one frame
    mock_cap.read.return_value = (True, MagicMock())  # Mock a frame
    mock_video_capture.return_value = mock_cap

    # Mock analyze_frame function
    mocker.patch(
        "app.analyze_frame",
        return_value=[{"class": "person", "confidence": 0.8, "box": [10, 20, 30, 40]}],
    )

    # Mock the upload file as a bytes object
    file_content = BytesIO(b"fake video data")
    response = client.post(
        "/analyze-video/", files={"file": ("test_video.mp4", file_content, "video/mp4")}
    )

    assert response.status_code == 200
    assert "frames" in response.json()
    assert len(response.json()["frames"]) == 1
    assert response.json()["frames"][0] == [
        {"class": "person", "confidence": 0.8, "box": [10, 20, 30, 40]}
    ]
