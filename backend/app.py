"""
Flask Backend for SafePath - Driver Drowsiness Detection
"""
import atexit
import cv2
import time
import threading

from flask import Flask, Response, jsonify, send_from_directory
from flask_cors import CORS

from drowsiness_detector import DrowsinessDetector

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

detector = DrowsinessDetector()
camera = None
lock = threading.Lock()
stop_event = threading.Event()

latest_jpeg = None


def _default_status():
    return {
        "status": "Normal",
        "drowsiness_score": 0,
        "trigger_audio": False,
        "timestamp": "",
        "metrics": {
            "ear": 0.0,
            "mar": 0.0,
            "blink_count": 0,
            "yawn_count": 0,
            "eyes_closed": False,
            "is_yawning": False,
        },
        "no_face_detected": False,
    }


latest_status = _default_status()


def _build_status_payload(detection_results):
    """Build a JSON-safe status payload from raw detection results."""
    eye_data = detection_results.get("eye_data", {})
    yawn_data = detection_results.get("yawn_data", {})
    alert_info = detection_results.get("alert_info", {})

    return {
        "status": alert_info.get("status", "Normal"),
        "drowsiness_score": int(alert_info.get("drowsiness_score", 0)),
        "trigger_audio": bool(alert_info.get("trigger_audio", False)),
        "timestamp": alert_info.get("timestamp", ""),
        "metrics": {
            "ear": float(eye_data.get("avg_ear", 0) or 0),
            "mar": float(yawn_data.get("mar", 0) or 0),
            "blink_count": int(eye_data.get("blink_count", 0) or 0),
            "yawn_count": int(yawn_data.get("yawn_count", 0) or 0),
            "eyes_closed": bool(eye_data.get("eyes_closed", False)),
            "is_yawning": bool(yawn_data.get("is_yawning", False)),
        },
        "no_face_detected": bool(detection_results.get("no_face_detected", False)),
    }


def get_camera():
    """Initialize and return camera."""
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
    return camera


def detection_loop():
    """Continuously process camera frames and publish status + video."""
    global latest_jpeg, latest_status

    cam = get_camera()
    fps_start_time = time.time()
    fps_frame_count = 0
    fps = 0.0

    while not stop_event.is_set():
        success, frame = cam.read()
        if not success:
            time.sleep(0.01)
            continue

        processed_frame, detection_results = detector.process_frame(frame)
        status_payload = _build_status_payload(detection_results)

        fps_frame_count += 1
        if fps_frame_count >= 10:
            fps = fps_frame_count / (time.time() - fps_start_time)
            fps_start_time = time.time()
            fps_frame_count = 0

        cv2.putText(
            processed_frame,
            f"FPS: {fps:.1f}",
            (10, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        _, buffer = cv2.imencode(".jpg", processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        with lock:
            latest_jpeg = buffer.tobytes()
            latest_status = status_payload


def start_detection_thread():
    """Start the background detection thread once."""
    thread = threading.Thread(target=detection_loop, daemon=True)
    thread.start()


_detection_started = False


def ensure_detection_started():
    """Start detection exactly once."""
    global _detection_started
    if not _detection_started:
        start_detection_thread()
        _detection_started = True


def cleanup():
    """Release resources on shutdown."""
    stop_event.set()
    detector.cleanup()
    if camera is not None:
        camera.release()


atexit.register(cleanup)


@app.route("/")
def index():
    """Serve the main dashboard."""
    ensure_detection_started()
    return send_from_directory(app.static_folder, "index.html")


@app.route("/video_feed")
def video_feed():
    """Video streaming route."""
    ensure_detection_started()

    def generate_frames():
        while True:
            with lock:
                frame_bytes = latest_jpeg

            if frame_bytes is None:
                time.sleep(0.05)
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/drowsiness_status")
def drowsiness_status():
    """Return current drowsiness detection status."""
    ensure_detection_started()
    with lock:
        response = dict(latest_status)
        response["metrics"] = dict(latest_status.get("metrics", {}))

    resp = jsonify(response)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return resp


@app.route("/session_data")
def session_data():
    """Return session statistics."""
    stats = detector.get_current_status()

    return jsonify(
        {
            "current_status": stats["status"],
            "total_blinks": stats["blink_count"],
            "total_yawns": stats["yawn_count"],
            "alert_history": stats["alert_stats"]["alert_history"],
            "total_alerts": stats["alert_stats"]["total_alerts"],
        }
    )


@app.route("/reset_session", methods=["POST"])
def reset_session():
    """Reset the current detection session."""
    detector.reset()
    return jsonify({"status": "success", "message": "Session reset"})


@app.errorhandler(404)
def not_found(_error):
    """Handle 404 errors."""
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("SafePath - Driver Drowsiness Detection System")
        print("=" * 60)
        print("\nStarting Flask server...")
        ensure_detection_started()
        print("\nAccess the dashboard at: http://127.0.0.1:5000")
        print("\nPress CTRL+C to stop the server\n")
        print("=" * 60)

        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        cleanup()
        print("Cleanup complete. Goodbye!")
