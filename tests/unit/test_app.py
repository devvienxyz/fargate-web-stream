import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, mock_open
from src.app import app, load_object_class_list, analyze_frame


client = TestClient(app)


@pytest.fixture
def mock_obj_class_list():
    return {"0": "person", "1": "car"}


@pytest.mark.unit
def test_load_object_class_list_success(mocker, mock_obj_class_list):
    mock_open_file = mock_open(read_data='{"classes": {"0": "person", "1": "car"}}')
    mocker.patch("builtins.open", mock_open_file)
    result = load_object_class_list()
    assert result == mock_obj_class_list


@pytest.mark.unit
def test_load_object_class_list_file_not_found(mocker):
    mocker.patch("builtins.open", side_effect=FileNotFoundError)
    result = load_object_class_list()
    assert result == []


@pytest.mark.unit
def test_analyze_frame(mocker, mock_obj_class_list):
    # Mock YOLO model output
    mock_model = mocker.patch("app.model")
    mock_result = MagicMock()
    mock_box = MagicMock()
    mock_box.xyxy = [[10, 20, 30, 40]]
    mock_box.conf = [0.8]
    mock_box.cls = [0]
    mock_result.boxes = [mock_box]
    mock_model.return_value = [mock_result]

    # Mock object classes list
    mocker.patch("app.obj_clss_list", mock_obj_class_list)

    # Test with a sample frame
    frame = MagicMock()
    detections = analyze_frame(frame)

    expected_detection = {"class": "person", "confidence": 0.8, "box": [10, 20, 30, 40]}
    assert detections == [expected_detection]
