import json
import time

import cv2
import numpy as np
import redis

from configs.loader import cfg
from logs.log_handler import logger
from modules.base_stream import BaseCamera

pre_id = {}
pre_frame_bytes = {}


class Camera(BaseCamera):
    def __init__(self, device, conn):
        super(Camera, self).__init__(device, conn)

    @staticmethod
    def draw(frame, metadata):
        if metadata is None:
            return frame
        objects = metadata["objects"]
        for obj in objects:
            bbox = list(map(int, obj["bbox"]))
            # id = obj["id"]
            frame = cv2.rectangle(
                frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 2
            )
            # if obj["face_bbox"]:
            #     face_bbox = list(map(int, obj["face_bbox"]))
            #     frame = cv2.rectangle(
            #         frame,
            #         (face_bbox[0], face_bbox[1]),
            #         (face_bbox[2], face_bbox[3]),
            #         (0, 0, 255),
            #         2,
            #     )

            display_text = "fire"
            # if obj["metadata"]["metadata"] is None:
            #     display_text = f"{id}"
            # else:
            #     display_text = f"{id} - {obj['metadata']['score']:.2f} - {obj['metadata']['metadata']['person_name']}"
            Camera.write_text_on_background(frame, display_text, bbox[0], bbox[1])
        return frame

    @staticmethod
    def draw_text_box_on_image(
        image, text, color=(0, 0, 255), top_right=(1280 - 20, 20)
    ):
        # Split text into lines
        lines = text.split("\n")

        # Get text sizes
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 2
        thickness = 2

        # Calculate maximum width and total height
        max_width = 0
        total_height = 0
        line_heights = []

        for line in lines:
            (line_width, line_height), baseline = cv2.getTextSize(
                line, font, font_scale, thickness
            )
            max_width = max(max_width, line_width)
            total_height += line_height + baseline
            line_heights.append((line_height, baseline))

        # Calculate box coordinates using top_right parameter
        padding = 30
        x = top_right[0] - (
            max_width + 2 * padding
        )  # Subtract box width from x coordinate
        y = top_right[1]  # Use y coordinate as is

        box_coords = [
            (x, y),
            (x + max_width + 2 * padding, y),
            (x + max_width + 2 * padding, y + total_height + 2 * padding),
            (x, y + total_height + 2 * padding),
        ]

        # Create overlay with the same color as border
        overlay = image.copy()
        cv2.fillPoly(overlay, [np.array(box_coords, np.int32)], color)

        # Apply transparency
        alpha = 0.8
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)

        # Draw border
        cv2.polylines(image, [np.array(box_coords, np.int32)], True, color, thickness=2)

        # Draw each line of text
        current_y = y + padding
        for i, line in enumerate(lines):
            line_height, baseline = line_heights[i]
            bonus = 0 if i == 0 else 10
            current_y += line_height + bonus
            cv2.putText(
                image,
                line,
                (x + padding, current_y),
                font,
                font_scale,
                (0, 0, 0),
                thickness,
            )
            current_y += baseline

        return image

    @staticmethod
    def write_text_on_background(
        frame,
        label,
        x,
        y,
        font_color=(0, 0, 0),
        rect_color=(230, 230, 230),
        font_scale=0.7,
        font_thickness=1,
    ):
        # Get the size of the text box
        (text_width, text_height), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
        )
        # Create a purple rectangle background
        rect_x1, rect_y1 = x, y - text_height
        rect_x2, rect_y2 = x + text_width, y
        cv2.rectangle(
            frame, (rect_x1, rect_y1), (rect_x2, rect_y2), rect_color, cv2.FILLED
        )
        # Put the label text on top of the rectangle
        cv2.putText(
            frame,
            label,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            font_color,
            font_thickness,
        )
        return frame

    @staticmethod
    def get_last_frame(camera_id, conn, resize=None):
        """Gets latest tracked frame to view on web"""
        global pre_id
        global pre_frame_bytes
        if camera_id not in pre_id:
            pre_id[camera_id] = 0
        if camera_id not in pre_frame_bytes:
            pre_frame_bytes[camera_id] = None
        # topic = f"business_service:{camera_id}"
        topic = f"ai_service:{camera_id}"
        p = conn.pipeline()
        p.xrevrange(topic, count=1)  # Latest tracked frame
        p_tuple = p.execute()
        msg = p_tuple[0]

        if msg:
            id_ = msg[0][0].decode("utf-8")
            if pre_id[camera_id] == id_:
                return pre_frame_bytes[camera_id]
            pre_id[camera_id] = id_
            metadata = msg[0][1]["metadata".encode("utf-8")]
            metadata = json.loads(metadata)
            logger.debug(f"{metadata}")
            # logger.debug(f"{ msg[0][1]}")
            # frame_bytes = msg[0][1]["frame".encode("utf-8")]
            frame_bytes = msg[0][1]["frame".encode("utf-8")]
            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), -1)
            # frame = np.array(frame)
            frame = Camera.draw(frame, metadata)
            retval, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = np.array(buffer).tobytes()
            pre_frame_bytes[camera_id] = frame_bytes
            return frame_bytes
        else:
            # logger.info("Dont have msg")
            return None

    @staticmethod
    def frames(camera_id, conn):
        while True:
            yield Camera.get_last_frame(camera_id, conn)


class CameraStream(object):
    def __init__(self, conn_pool, camera_id):
        self.camera_id = camera_id
        self.host = "ai-fire-tranship-service"
        self.port = 6379  # Sử dụng port mặc định của Redis
        conn = redis.Redis(host=self.host, port=self.port)
        if not conn.ping():
            raise Exception("Redis unavailable")
        self.camera = Camera(camera_id, conn)

    def get_last_frame(self):
        final_frame = self.camera.get_frame(self.camera_id)
        return final_frame


def gen_cameras(stream: CameraStream, record=False):
    fr_count = 0
    start_time = time.time()
    period_time = time.time()
    while True:
        start_vis_time = time.time()
        frame = stream.get_last_frame()
        if frame is not None:
            fr_count += 1
            fps = round(fr_count / (time.time() - start_time), 2)

            if time.time() - period_time > 20:  # log FPS each 10 seconds
                logger.debug(f"CAM gen_camera time -period > 20 {stream.camera_id}")
                period_time = time.time()
                fr_count = 0
                start_time = time.time()
            sleep_time = 1.0 / cfg["common"]["stream"]["target_fps"] - (
                time.time() - start_vis_time
            )
            if sleep_time > 0:
                time.sleep(sleep_time)
            logger.debug(f"fps {fps}")
            yield (
                b"--frame\r\n"
                b"Pragma-directive: no-cache\r\n"
                b"Cache-directives: no-cache\r\n"
                b"Cache-control: no-cache\r\n"
                b"Pragma: no-cache\r\n"
                b"Expires: 0\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n"
            )
