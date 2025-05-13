# File: modules/entities/redis/redis_pipeline.py
import json
import time
from threading import Event
import redis
import logging
from modules.controllers.business_logic import FireSmokeMonitoringController
from modules.entities.notify.telegram import TelegramHandler

logger = logging.getLogger(__name__)

class FireSmokeMonitoringPipeline:
    """
    Pipeline communicates with Redis:
        - Read data from ai_service stream 
        - Call controller to process business logic 
        - Send result to Redis 
    """
    def __init__(self, camera_info, telegram_handler, redis_host="ai-fire-tranship-service", redis_port=6379, stream_maxlen=1000):
        self.redis_conn = redis.Redis(host=redis_host, port=redis_port)
        if not self.redis_conn.ping():
            raise Exception("Redis unavailable")
        self.camera_info = camera_info
        self.pre_last_id = None
        self.stream_maxlen = stream_maxlen  
        self.fire_smoke_monitor = FireSmokeMonitoringController(telegram_handler)

    def get_last(self, topic):
        try:
            p = self.redis_conn.pipeline()
            p.xrevrange(topic, count=1)
            msgs = p.execute()[0]
            if msgs:
                id_ = msgs[0][0]
                if self.pre_last_id == id_:
                    return None, None
                self.pre_last_id = id_
                msg_fields = msgs[0][1]
                if b"metadata" not in msg_fields or b"frame" not in msg_fields:
                    return None, None
                metadata = json.loads(msg_fields[b"metadata"])
                frame_bytes = msg_fields.get(b"frame", None)
                if frame_bytes is None:
                    logger.error("Frame data is missing in the Redis message.")
                    return None, None
                return metadata, frame_bytes
            return None, None
        except Exception as e:
            logger.error(f"Failed to get last data: {e}")
            return None, None

    def start(self, stop_event: Event):
        topic_recv = f"ai_service:{self.camera_info['id']}"
        topic_sent = f"business_service:{self.camera_info['id']}"
        logger.info(f"Starting pipeline for camera: {self.camera_info['id']}")
        counter = 0
        while not stop_event.is_set():
            metadata, frame_bytes = self.get_last(topic_recv)
            if metadata is None:
                time.sleep(0.01)
                counter += 1
                if counter % 1000 == 0:
                    logger.debug("Waiting for messages...")
                continue

            counter = 0
            tobjs = metadata.get("objects", [])
            tobjs, fire_notify_ids = self.fire_smoke_monitor.update(tobjs, frame_bytes)

            if fire_notify_ids:
                metadata_to_save = {
                    "camera_id": self.camera_info["id"],
                    "frame_id": metadata.get("frame_id"),
                    "timestamp": metadata.get("timestamp"),
                    "fire_notify_ids": fire_notify_ids,
                }
                msg = {"metadata": json.dumps(metadata_to_save)}
                if frame_bytes:
                    msg["evidence"] = frame_bytes
                self.redis_conn.xadd(topic_sent, msg, maxlen=self.stream_maxlen)
                logger.info(f"Sent fire alerts to Redis: {fire_notify_ids}")
            time.sleep(0.01)
