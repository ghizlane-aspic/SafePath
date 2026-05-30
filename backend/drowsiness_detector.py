"""
Drowsiness Detection Engine using MediaPipe Face Landmarker
"""
import os
import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from utils.alert_manager import AlertManager
from utils.eye_tracker import EyeTracker
from utils.yawn_detector import YawnDetector

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "face_landmarker.task")


class DrowsinessDetector:
    def __init__(self):
        """Initialize drowsiness detector with MediaPipe Face Landmarker."""
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Face landmarker model not found at {MODEL_PATH}. "
                "Download it from MediaPipe model storage."
            )

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
        self.start_time = time.time()

        # Eye-first tuning: closed eyes alone must trigger alerts
        self.eye_tracker = EyeTracker(ear_threshold=0.26, consecutive_frames=12)
        self.yawn_detector = YawnDetector(mar_threshold=0.60, consecutive_frames=12)
        self.alert_manager = AlertManager()

        self.frame_count = 0

    def process_frame(self, frame):
        """
        Process a single video frame for drowsiness detection.

        Args:
            frame: BGR image from webcam

        Returns:
            tuple: (processed_frame, detection_results)
        """
        self.frame_count += 1
        frame_height, frame_width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((time.time() - self.start_time) * 1000)

        results = self.face_landmarker.detect_for_video(mp_image, timestamp_ms)

        annotated_frame = frame.copy()
        eye_data = {
            "avg_ear": 0.0,
            "blink_count": self.eye_tracker.total_blinks,
            "eyes_closed": False,
            "closed_frames": 0,
            "is_drowsy": False,
        }
        yawn_data = {
            "mar": 0.0,
            "yawn_count": self.yawn_detector.total_yawns,
            "yawn_detected": False,
            "is_yawning": False,
        }
        no_face_detected = not results.face_landmarks

        if results.face_landmarks:
            face_landmarks = results.face_landmarks[0]

            eye_data = self.eye_tracker.process_frame(
                face_landmarks, frame_width, frame_height
            )
            yawn_data = self.yawn_detector.process_frame(
                face_landmarks, frame_width, frame_height
            )

            self._draw_eye_landmarks(annotated_frame, eye_data)
            self._draw_mouth_landmarks(annotated_frame, yawn_data)

            ear_text = f"EAR: {eye_data['avg_ear']:.2f}"
            cv2.putText(
                annotated_frame,
                ear_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            mar_text = f"MAR: {yawn_data['mar']:.2f}"
            cv2.putText(
                annotated_frame,
                mar_text,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
        else:
            cv2.putText(
                annotated_frame,
                "NO FACE DETECTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        drowsiness_score = self.alert_manager.calculate_drowsiness_score(
            eye_data, yawn_data, no_face_detected
        )
        alert_info = self.alert_manager.update_status(drowsiness_score)

        status = alert_info["status"]
        status_color = self._get_status_color(status)
        cv2.putText(
            annotated_frame,
            f"Status: {status}",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2,
        )
        cv2.putText(
            annotated_frame,
            f"Drowsiness: {drowsiness_score}%",
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2,
        )

        if status == "Alert":
            overlay = annotated_frame.copy()
            cv2.rectangle(
                overlay, (0, 0), (frame_width, frame_height), (0, 0, 255), -1
            )
            annotated_frame = cv2.addWeighted(annotated_frame, 0.7, overlay, 0.3, 0)

            warning_text = "DROWSINESS DETECTED!"
            text_size = cv2.getTextSize(
                warning_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3
            )[0]
            text_x = (frame_width - text_size[0]) // 2
            text_y = (frame_height + text_size[1]) // 2
            cv2.putText(
                annotated_frame,
                warning_text,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (255, 255, 255),
                3,
            )

        detection_results = {
            "eye_data": eye_data,
            "yawn_data": yawn_data,
            "alert_info": alert_info,
            "no_face_detected": no_face_detected,
            "frame_count": self.frame_count,
        }

        return annotated_frame, detection_results

    def _draw_eye_landmarks(self, frame, eye_data):
        """Draw eye landmark points on the frame."""
        color = (0, 0, 255) if eye_data.get("eyes_closed") else (0, 255, 255)
        for eye_key in ("left_eye_landmarks", "right_eye_landmarks"):
            landmarks = eye_data.get(eye_key)
            if landmarks is None:
                continue
            for point in landmarks:
                cv2.circle(frame, tuple(point), 2, color, -1)

    def _draw_mouth_landmarks(self, frame, yawn_data):
        """Draw mouth landmark points on the frame."""
        landmarks = yawn_data.get("mouth_landmarks")
        if landmarks is None:
            return
        color = (0, 165, 255) if yawn_data.get("is_yawning") else (255, 255, 0)
        for point in landmarks:
            cv2.circle(frame, tuple(point), 3, color, -1)

    def _get_status_color(self, status):
        """Get BGR color for status text."""
        colors = {
            "Normal": (0, 255, 0),
            "Warning": (0, 255, 255),
            "Alert": (0, 0, 255),
        }
        return colors.get(status, (255, 255, 255))

    def get_current_status(self):
        """Get current drowsiness detection status."""
        return {
            "status": self.alert_manager.current_status,
            "blink_count": self.eye_tracker.total_blinks,
            "yawn_count": self.yawn_detector.total_yawns,
            "alert_stats": self.alert_manager.get_alert_stats(),
        }

    def reset(self):
        """Reset all trackers."""
        self.alert_manager.reset()
        self.eye_tracker.reset()
        self.yawn_detector.reset()
        self.frame_count = 0
        self.start_time = time.time()

    def cleanup(self):
        """Release MediaPipe resources."""
        self.face_landmarker.close()
