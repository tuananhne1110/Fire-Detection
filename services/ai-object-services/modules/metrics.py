from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics for object detection
detection_counter = Counter(
    'object_detection_total',
    'Total number of objects detected',
    ['class']
)

detection_latency = Histogram(
    'object_detection_latency_seconds',
    'Time spent processing frames',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

frame_processing_time = Histogram(
    'frame_processing_seconds',
    'Time spent processing each frame',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

active_cameras = Gauge(
    'active_cameras',
    'Number of active camera streams'
)

def track_detection(class_name):
    detection_counter.labels(class=class_name).inc()

def track_processing_time():
    return detection_latency.time()

def track_frame_time():
    return frame_processing_time.time() 