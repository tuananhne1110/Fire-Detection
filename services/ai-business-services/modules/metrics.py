from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics for business logic
fire_alert_counter = Counter(
    'fire_alert_total',
    'Total number of fire alerts',
    ['camera_id']
)

smoke_alert_counter = Counter(
    'smoke_alert_total',
    'Total number of smoke alerts',
    ['camera_id']
)

notification_latency = Histogram(
    'notification_latency_seconds',
    'Time spent sending notifications',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

active_alerts = Gauge(
    'active_alerts',
    'Number of active alerts',
    ['type']
)

def track_fire_alert(camera_id):
    fire_alert_counter.labels(camera_id=camera_id).inc()
    active_alerts.labels(type='fire').inc()

def track_smoke_alert(camera_id):
    smoke_alert_counter.labels(camera_id=camera_id).inc()
    active_alerts.labels(type='smoke').inc()

def track_notification_time():
    return notification_latency.time()

def clear_alert(type):
    active_alerts.labels(type=type).dec() 