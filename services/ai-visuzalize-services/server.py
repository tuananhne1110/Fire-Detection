import redis
from flask import Flask, Response

from configs.loader import cfg
from logs.log_handler import logger
from modules.cam_stream import CameraStream, gen_cameras

app = Flask(__name__)


@app.route("/ai_stream/fire/<camera_id>")
def ai_stream(camera_id):
    redis_conn_pool = redis.ConnectionPool(
        host=cfg["common"]["redis"]["host"], port=cfg["common"]["redis"]["port"]
    )
    logger.debug(f"CAM: {camera_id}")
    return Response(
        gen_cameras(CameraStream(redis_conn_pool, camera_id)),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/")
def health():
    return {"status": 200}
