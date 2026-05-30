"""
Alert Manager - Handle alert levels and notifications
"""
import time
from datetime import datetime


class AlertManager:
    def __init__(self):
        """Initialize Alert Manager"""
        self.alert_history = []
        self.current_status = "Normal"
        self.last_alert_time = None
        self.alert_cooldown = 5  # seconds between alerts
        
        # Alert thresholds (aligned with dashboard: Warning 30+, Alert 70+)
        self.NORMAL_THRESHOLD = 30
        self.WARNING_THRESHOLD = 70
    
    def calculate_drowsiness_score(self, eye_data, yawn_data, no_face_detected=False):
        """
        Calculate overall drowsiness score (0-100).
        
        Args:
            eye_data: Dictionary from EyeTracker
            yawn_data: Dictionary from YawnDetector
            no_face_detected: Boolean indicating if face is not visible
        
        Returns:
            int: Drowsiness score (0-100)
        """
        score = 0
        closed_frames = eye_data.get('closed_frames', 0)

        # Eye closure is the primary signal — must reach Alert without yawning
        if eye_data.get('is_drowsy', False):
            score += 85
        elif eye_data.get('eyes_closed', False):
            score += min(80, 35 + closed_frames * 3)

        # Yawning adds to the score but is not required
        if yawn_data.get('yawn_detected', False):
            score += 15
        elif yawn_data.get('is_yawning', False):
            score += 8

        # No face detected (10 points) - driver looking away or head dropped
        if no_face_detected:
            score += 10

        return min(score, 100)
    
    def determine_alert_level(self, drowsiness_score):
        """
        Determine alert level based on drowsiness score.
        
        Args:
            drowsiness_score: Score from 0-100
        
        Returns:
            str: Alert level ("Normal", "Warning", "Alert")
        """
        if drowsiness_score >= self.WARNING_THRESHOLD:
            return "Alert"
        elif drowsiness_score >= self.NORMAL_THRESHOLD:
            return "Warning"
        else:
            return "Normal"
    
    def should_trigger_alert(self):
        """
        Check if enough time has passed since last alert (cooldown).
        
        Returns:
            bool: True if alert should be triggered
        """
        if self.last_alert_time is None:
            return True
        
        time_since_alert = time.time() - self.last_alert_time
        return time_since_alert >= self.alert_cooldown
    
    def update_status(self, drowsiness_score):
        """
        Update the current status and trigger alerts if needed.
        
        Args:
            drowsiness_score: Current drowsiness score
        
        Returns:
            dict: Alert information
        """
        new_status = self.determine_alert_level(drowsiness_score)
        status_changed = new_status != self.current_status
        
        # Trigger alert if status is "Alert" and cooldown passed
        trigger_audio = False
        if new_status == "Alert" and self.should_trigger_alert():
            trigger_audio = True
            self.last_alert_time = time.time()
            
            # Log alert
            self.alert_history.append({
                'timestamp': datetime.now().isoformat(),
                'score': drowsiness_score,
                'status': new_status
            })
        
        self.current_status = new_status
        
        return {
            'status': new_status,
            'status_changed': status_changed,
            'trigger_audio': trigger_audio,
            'drowsiness_score': drowsiness_score,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_alert_stats(self):
        """
        Get statistics about alerts.
        
        Returns:
            dict: Alert statistics
        """
        total_alerts = len(self.alert_history)
        
        return {
            'total_alerts': total_alerts,
            'current_status': self.current_status,
            'last_alert': self.alert_history[-1] if total_alerts > 0 else None,
            'alert_history': self.alert_history[-10:]  # Last 10 alerts
        }
    
    def reset(self):
        """Reset alert manager"""
        self.alert_history = []
        self.current_status = "Normal"
        self.last_alert_time = None
