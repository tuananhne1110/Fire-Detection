# File: business_main.py
import logging
from threading import Event
from modules.entities.notify.telegram import TelegramHandler
from modules.entities.redis.redis_pipeline import FireSmokeMonitoringPipeline

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration Telegram Bot
bot_token = "8076921477:AAElPFyCAWXe_eaTY8m9kBXf9taFZh2AnCE"
chat_id = "-4700416302"
telegram_handler = TelegramHandler(bot_token, chat_id)

camera_info = {"id": "cam_2", "name": "Camera Hầm gửi xe"}

pipeline = FireSmokeMonitoringPipeline(camera_info, telegram_handler)
stop_event = Event()

print("Starting business_service pipeline. Press Ctrl+C to stop.")
try:
    pipeline.start(stop_event)
except KeyboardInterrupt:
    stop_event.set()
    print("Stopping pipeline...")
