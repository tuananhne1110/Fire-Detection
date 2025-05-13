from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics for visualization
stream_requests = Counter(
    'stream_requests_total',
    'Total number of stream requests',
    ['camera_id']
)

stream_errors = Counter(
    'stream_errors_total',
    'Total number of stream errors',
    ['camera_id', 'error_type']
)

stream_latency = Histogram(
    'stream_latency_seconds',
    'Time spent streaming frames',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

active_streams = Gauge(
    'active_streams',
    'Number of active video streams'
)

def track_stream_request(camera_id):
    stream_requests.labels(camera_id=camera_id).inc()
    active_streams.inc()

def track_stream_error(camera_id, error_type):
    stream_errors.labels(camera_id=camera_id, error_type=error_type).inc()

def track_stream_time():
    return stream_latency.time()

def end_stream():
    active_streams.dec() 