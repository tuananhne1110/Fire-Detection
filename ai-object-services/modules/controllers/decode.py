# File: modules/controllers/decode.py
import json
import os
import time
import queue
import threading
from threading import Thread, Event

import cv2

from configs.loader import cfg
from logs.log_handler import logger
from modules.entities.camera.camera_info import Camera


class DecodeController:
    def __init__(self, queue_frame):
        self.queue_frame = queue_frame
        self.cam_threads = dict()
        self.cam_del_events = dict()
        self.cameras = dict()

    def init_decode_cameras(self):
        """Read config files and start threads for each camera"""
        cameras = cfg.get("cameras", [])
        for cam in cameras:
            self.create_decode_thread(cam["id"], cam["url"])

    def create_decode_thread(self, cam_id, cam_url):
        """Create and start a camera decoding thread"""
        cam_entity = Camera(cam_id, cam_url)
        del_event = Event()
        t = Thread(target=self.decode_camera, args=(cam_entity, del_event))
        t.start()
        self.cam_threads[cam_id] = t
        self.cam_del_events[cam_id] = del_event
        self.cameras[cam_id] = cam_entity

    def send_msg(self, msg, my_queue):
        """Send message to queue with non-blocking put"""
        try:
            my_queue.put_nowait(msg)
            # logger.debug(f"Message sent to queue: {msg}")
            # print("Message sent to queue:", msg)
        except queue.Full:
            try:
                my_queue.get_nowait()
                my_queue.put_nowait(msg)
                # logger.debug(f"Queue was full; replaced old message with: {msg}")
                # print("Queue full; replaced old message with:", msg)
            except queue.Empty:
                pass

    def decode_camera(self, camera_entity, del_event):
        """Thread function for decoding camera stream"""
        camera_id = camera_entity.id
        url = camera_entity.url

        logger.debug(f"Camera {camera_id} TID: {threading.get_native_id()}")

        cap = cv2.VideoCapture(url)
        fps_cfg = cfg.get("common", {}).get("camera", {})

        n_frames = 0
        start_time = time.time()

        # Configuration for pushing frames
        target_push_fps = fps_cfg.get("push_fps", 1)
        pushed_frame_count = 0
        start_push_time = time.time()

        while True:
            if del_event.is_set():
                logger.debug(f"CAM_ID: {camera_id} - DECODE - DELETED")
                break

            ret, frame = cap.read()

            if not ret:
                logger.debug(
                    f"CAM_ID: {camera_id} - DECODE - Cannot read video from {url}, retry..."
                )
                cap = cv2.VideoCapture(url)
                time.sleep(2)
                continue

            # Throttle push rate
            push_fps = pushed_frame_count / (time.time() - start_push_time + 1e-7)
            if push_fps >= target_push_fps:
                continue


            pushed_frame_count += 1
            n_frames += 1
            timestamp = time.time()
            msg = {
                "camera_id": camera_id,
                "timestamp": timestamp,
                "metadata": {
                    "frame": frame,  
                    "id frame": n_frames,
                },
            }

            self.send_msg(msg, self.queue_frame)

    def run(self, events=None):
        logger.debug(f"Decode Controller PID: {os.getpid()}")
        self.init_decode_cameras()
