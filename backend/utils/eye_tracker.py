"""
Eye Tracking Module - Calculate Eye Aspect Ratio (EAR) for drowsiness detection
"""
import numpy as np


def euclidean_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt(np.sum((np.array(point1) - np.array(point2)) ** 2))


class EyeTracker:
    def __init__(self, ear_threshold=0.25, consecutive_frames=20):
        """
        Initialize Eye Tracker
        
        Args:
            ear_threshold: EAR below this value indicates closed eyes (default: 0.25)
            consecutive_frames: Number of consecutive frames with closed eyes to trigger alert
        """
        self.EAR_THRESHOLD = ear_threshold
        self.CONSECUTIVE_FRAMES = consecutive_frames
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_counter = 0
        
        # MediaPipe Face Mesh landmark indices for eyes
        self.LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    
    def calculate_ear(self, eye_landmarks):
        """
        Calculate Eye Aspect Ratio (EAR) for given eye landmarks.
        
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        
        Args:
            eye_landmarks: List of 6 (x, y) coordinates for eye landmarks
        
        Returns:
            float: Eye Aspect Ratio value
        """
        # Compute the euclidean distances between the two sets of vertical eye landmarks
        A = euclidean_distance(eye_landmarks[1], eye_landmarks[5])
        B = euclidean_distance(eye_landmarks[2], eye_landmarks[4])
        
        # Compute the euclidean distance between the horizontal eye landmarks
        C = euclidean_distance(eye_landmarks[0], eye_landmarks[3])
        
        # Calculate EAR
        ear = (A + B) / (2.0 * C)
        return ear
    
    def extract_eye_landmarks(self, face_landmarks, eye_indices, frame_width, frame_height):
        """
        Extract eye landmark coordinates from MediaPipe face mesh results.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            eye_indices: List of landmark indices for specific eye
            frame_width: Width of video frame
            frame_height: Height of video frame
        
        Returns:
            numpy array: Array of (x, y) coordinates for eye landmarks
        """
        landmarks = []
        for idx in eye_indices:
            landmark = self._get_landmark(face_landmarks, idx)
            x = int(landmark.x * frame_width)
            y = int(landmark.y * frame_height)
            landmarks.append([x, y])
        
        return np.array(landmarks)

    def _get_landmark(self, face_landmarks, idx):
        """Support both legacy and Tasks API landmark containers."""
        if hasattr(face_landmarks, "landmark"):
            return face_landmarks.landmark[idx]
        return face_landmarks[idx]
    
    def process_frame(self, face_landmarks, frame_width, frame_height):
        """
        Process a single frame to detect eye closure and blinks.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            frame_width: Width of video frame
            frame_height: Height of video frame
        
        Returns:
            dict: Dictionary containing EAR values, blink info, and drowsiness status
        """
        # Extract eye landmarks
        left_eye = self.extract_eye_landmarks(face_landmarks, self.LEFT_EYE_INDICES, frame_width, frame_height)
        right_eye = self.extract_eye_landmarks(face_landmarks, self.RIGHT_EYE_INDICES, frame_width, frame_height)
        
        # Calculate EAR for both eyes
        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)
        
        # Average EAR — also check each eye for partial/drowsy closure
        avg_ear = (left_ear + right_ear) / 2.0
        min_ear = min(left_ear, right_ear)

        # Closed if average is low, or both eyes are clearly shutting
        eyes_closed = (
            avg_ear < self.EAR_THRESHOLD
            or min_ear < (self.EAR_THRESHOLD - 0.03)
        )
        
        # Track consecutive frames with closed eyes
        if eyes_closed:
            self.frame_counter += 1
        else:
            # Detect blink (eyes were closed and now open)
            if self.frame_counter >= 3:  # Minimum frames for a blink
                self.total_blinks += 1
            self.frame_counter = 0
        
        # Determine if drowsy (eyes closed for too long)
        is_drowsy = self.frame_counter >= self.CONSECUTIVE_FRAMES
        
        return {
            'left_ear': round(left_ear, 3),
            'right_ear': round(right_ear, 3),
            'avg_ear': round(avg_ear, 3),
            'eyes_closed': eyes_closed,
            'blink_count': self.total_blinks,
            'closed_frames': self.frame_counter,
            'is_drowsy': is_drowsy,
            'left_eye_landmarks': left_eye,
            'right_eye_landmarks': right_eye
        }
    
    def reset(self):
        """Reset all counters"""
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_counter = 0
