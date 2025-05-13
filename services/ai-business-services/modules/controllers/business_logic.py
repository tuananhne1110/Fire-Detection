import time
import logging

logger = logging.getLogger(__name__)

class FireSmokeMonitoringController:
    def __init__(self, telegram_handler, window_size=75, threshold_window=0.8, max_center_movement=400, alert_interval=15):
        self.telegram_handler = telegram_handler
        self.window_size = window_size  
        self.threshold_window = threshold_window  
        self.max_center_movement = max_center_movement
        self.alert_interval = alert_interval 
        self.last_alert_time = None  
        self.frame_count = 0  
        self.fire_window = []  
    
    def update(self, tobjs, frame_bytes=None):
        self.frame_count += 1
        current_time = time.time()
        
        # Check if fire is detected
        fire_detected = self._is_fire_detected(tobjs)
        
        # Update sliding window
        self._update_fire_window(fire_detected)
        
        # Check if enough frames are available for evaluation
        if len(self.fire_window) == self.window_size:
            self._evaluate_fire_ratio(current_time, frame_bytes)
        
        return [], []
    
    def _is_fire_detected(self, tobjs):
        """Check if fire is detected in the frame."""
        return any(obj.get("cls") == 0 and obj.get("conf", 0.0) >= 0.2 for obj in tobjs)
    
    def _update_fire_window(self, fire_detected):
        """Update the list of frames with fire detection."""
        self.fire_window.append(1 if fire_detected else 0)
        if len(self.fire_window) > self.window_size:
            self.fire_window.pop(0)
    
    def _evaluate_fire_ratio(self, current_time, frame_bytes):
        """Evaluate the fire detection ratio and send an alert if necessary."""
        fire_ratio = sum(self.fire_window) / self.window_size
        logger.debug(f"Frame: {self.frame_count}, Fire Ratio: {fire_ratio:.2f}")
        
        if fire_ratio >= self.threshold_window and self._can_send_alert(current_time):
            self.send_alert(frame_bytes)
            self.last_alert_time = current_time
    
    def _can_send_alert(self, current_time):
        """Determine whether an alert can be sent based on time interval."""
        if self.last_alert_time is None:
            return True
        remaining_time = self.alert_interval - (current_time - self.last_alert_time)
        if remaining_time > 0:
            logger.debug(f"Fire detected but waiting {remaining_time:.2f}s before next alert.")
            return False
        return True
    
    def send_alert(self, frame_bytes):
        """Send an alert when fire is detected."""
        # self.telegram_handler.send_message("Warning: Fire Detected!", evidence=frame_bytes)
        logger.debug(f"ALERT SENT at Frame: {self.frame_count}, Time: {time.time():.2f}s")