# File: modules/entities/redis/redis_connection.py
import json
import redis 

from configs.loader import cfg 
from logs.log_handler import logger

class RedisConnection:
    def __init__(self):
        self.host = 'ai-fire-tranship-service'
        self.port = 6379  
        self.redis_conn = self._initialize_redis()
        self.pre_last_id = None 

    def _initialize_redis(self):
        try:
            redis_conn = redis.Redis(host=self.host, port=self.port)
            if not redis_conn.ping():
                logger.error("Redis unavailable")
            else:
                logger.debug("Redis init successfully")
            return redis_conn
        except Exception as e:
            logger.error(f"Failed to init Redis connection: {e}", exc_info=True)
            return None

    def get_last_message(self, topic):
        if self.redis_conn is None:
            return None
        
        try:
            p = self.redis_conn.pipeline()
            p.xrevrange(topic, count=1)
            msgs = p.execute()[0]
            if msgs:
                _id, data = msgs[0]
                if self.pre_last_id == _id:
                    return None 
                self.pre_last_id = _id
                metadata = json.loads(data[b"metadata"])
                frame_bytes = data[b"frame"]
                return {
                    "frame": frame_bytes,
                    "metadata": metadata,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get last data: {e}")
            return None 
        
    def send_message(self, msg, topic):
        if self.redis_conn is None:
            logger.error("Redis connection is not available!")
            return 
        try:
            result = self.redis_conn.xadd(topic, msg, maxlen=1)
            # logger.debug(f"Message sent to topic '{topic}': {msg} (ID: {result})")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
