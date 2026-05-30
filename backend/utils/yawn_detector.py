"""
Yawn Detection Module - Detect yawning using mouth aspect ratio
"""
import numpy as np


def euclidean_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt(np.sum((np.array(point1) - np.array(point2)) ** 2))


class YawnDetector:
    def __init__(self, mar_threshold=0.6, consecutive_frames=15):
        """
        Initialize Yawn Detector
        
        Args:
            mar_threshold: MAR above this value indicates yawning (default: 0.6)
            consecutive_frames: Number of consecutive frames to confirm yawn
        """
        self.MAR_THRESHOLD = mar_threshold
        self.CONSECUTIVE_FRAMES = consecutive_frames
        self.yawn_counter = 0
        self.total_yawns = 0
        self.frame_counter = 0
        
        # MediaPipe Face Mesh landmark indices for mouth
        # Outer lips landmarks
        self.MOUTH_INDICES = [61, 291, 0, 17, 269, 405]  # Top, bottom, left, right
    
    def calculate_mar(self, mouth_landmarks):
        """
        Calculate Mouth Aspect Ratio (MAR).
        
        MAR = (vertical distance) / (horizontal distance)
        
        Args:
            mouth_landmarks: List of (x, y) coordinates for mouth landmarks
        
        Returns:
            float: Mouth Aspect Ratio value
        """
        # Vertical distance (top to bottom)
        vertical = euclidean_distance(mouth_landmarks[0], mouth_landmarks[1])
        
        # Horizontal distance (left to right)
        horizontal = euclidean_distance(mouth_landmarks[2], mouth_landmarks[3])
        
        # Calculate MAR
        mar = vertical / horizontal if horizontal > 0 else 0
        return mar
    
    def extract_mouth_landmarks(self, face_landmarks, frame_width, frame_height):
        """
        Extract mouth landmark coordinates from MediaPipe face mesh results.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            frame_width: Width of video frame
            frame_height: Height of video frame
        
        Returns:
            list: List of (x, y) coordinates for key mouth points
        """
        # Get specific mouth landmarks
        top_lip = self._get_landmark(face_landmarks, 13)
        bottom_lip = self._get_landmark(face_landmarks, 14)
        left_corner = self._get_landmark(face_landmarks, 61)
        right_corner = self._get_landmark(face_landmarks, 291)
        
        landmarks = [
            [int(top_lip.x * frame_width), int(top_lip.y * frame_height)],
            [int(bottom_lip.x * frame_width), int(bottom_lip.y * frame_height)],
            [int(left_corner.x * frame_width), int(left_corner.y * frame_height)],
            [int(right_corner.x * frame_width), int(right_corner.y * frame_height)]
        ]
        
        return landmarks

    def _get_landmark(self, face_landmarks, idx):
        """Support both legacy and Tasks API landmark containers."""
        if hasattr(face_landmarks, "landmark"):
            return face_landmarks.landmark[idx]
        return face_landmarks[idx]
    
    def process_frame(self, face_landmarks, frame_width, frame_height):
        """
        Process a single frame to detect yawning.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            frame_width: Width of video frame
            frame_height: Height of video frame
        
        Returns:
            dict: Dictionary containing MAR values and yawn detection status
        """
        # Extract mouth landmarks
        mouth_landmarks = self.extract_mouth_landmarks(face_landmarks, frame_width, frame_height)
        
        # Calculate MAR
        mar = self.calculate_mar(mouth_landmarks)
        
        # Check if yawning
        is_yawning = mar > self.MAR_THRESHOLD
        
        # Track consecutive frames with mouth open
        if is_yawning:
            self.frame_counter += 1
        else:
            # Detect completed yawn
            if self.frame_counter >= self.CONSECUTIVE_FRAMES:
                self.total_yawns += 1
            self.frame_counter = 0
        
        # Confirm yawn if sustained for enough frames
        yawn_detected = self.frame_counter >= self.CONSECUTIVE_FRAMES
        
        return {
            'mar': round(mar, 3),
            'is_yawning': is_yawning,
            'yawn_count': self.total_yawns,
            'yawn_detected': yawn_detected,
            'mouth_landmarks': mouth_landmarks
        }
    
    def reset(self):
        """Reset all counters"""
        self.yawn_counter = 0
        self.total_yawns = 0
        self.frame_counter = 0
