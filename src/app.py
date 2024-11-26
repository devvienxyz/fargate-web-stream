import cv2
import ffmpeg
import json
import os
import shutil
import tempfile
import logging
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from io import BytesIO

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = FastAPI()
DEBUG = os.environ.get("DEBUG", 0)

# CORS
origins = ["http://localhost:3000", "http://127.0.0.1:3000"] if DEBUG else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

model = YOLO("yolo-Weights/yolov8n.pt")


def load_object_class_list():
    try:
        with open("objects.json", "r") as file:
            obj_clss = json.load(file)
            return obj_clss["classes"]
    except Exception:
        return []


obj_clss_list = load_object_class_list()


def convert_video_to_mp4(input_path, output_path):
    try:
        ffmpeg.input(input_path).output(
            output_path, vcodec="libx264", acodec="aac"
        ).run(overwrite_output=True)
    except ffmpeg.Error as e:
        # error_message = e.stderr.decode()  # Decode FFmpeg's stderr
        error_message = str(e)  # Decode FFmpeg's stderr
        logger.error(e)
        logger.error(f"FFmpeg error: {error_message}")
        raise HTTPException(status_code=400, detail=f"FFmpeg error: {error_message}")


def remux_video(input_path, output_path):
    try:
        ffmpeg.input(input_path).output(output_path, codec="copy").run(
            overwrite_output=True
        )
    except ffmpeg.Error as e:
        raise HTTPException(
            status_code=400, detail=f"FFmpeg remux error: {e.stderr.decode()}"
        )


def analyze_frame(frame):
    """Analyze a single frame using YOLO and return results."""
    results = model(frame)
    detections = []

    for r in results:
        boxes = r.boxes
        class_list = r.names

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
            confidence = round(float(box.conf[0]) * 100) / 100  # percent
            obj_class = int(box.cls[0])  # Object class index
            # class_name = obj_clss_list.get(str(obj_class), "Unknown")
            class_name = class_list.get(obj_class)
            detections.append(
                {"class": class_name, "confidence": confidence, "box": [x1, y1, x2, y2]}
            )
    return detections


def validate_video_file(filepath):
    try:
        ffmpeg.probe(filepath)
    except ffmpeg.Error as e:
        raise HTTPException(
            # status_code=400, detail=f"Invalid video file: {e.stderr.decode()}"
            status_code=400,
            detail=f"Invalid video file: {str(e)}",
        )


@app.post("/analyze-video/")
async def analyze_video(stream: UploadFile = File(...)):
    """Endpoint to receive video file and analyze frames."""
    frame_results = []

    try:
        # Save uploaded file
        input_video_path = stream.filename
        with open(input_video_path, "wb") as buffer:
            shutil.copyfileobj(stream.file, buffer)

        # Convert video to compatible format
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        processed_video = convert_video_to_mp4(input_video_path, temp_video.name)

        # Open video file
        cap = cv2.VideoCapture(processed_video)
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # frame_count += 1
            # # Analyze every 10th frame
            # if frame_count % 10 != 0:
            #     continue

            detections = analyze_frame(frame)
            frame_results.append(detections)

        cap.release()
        return {"frames": frame_results}

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return JSONResponse(status_code=400, content={"message": str(e)})

    finally:
        # Cleanup temporary files
        if os.path.exists(input_video_path):
            os.remove(input_video_path)
        if os.path.exists(temp_video.name):
            os.remove(temp_video.name)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
