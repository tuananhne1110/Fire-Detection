import cv2
import torch
from ultralytics import YOLO
from configs.loader import cfg

class YOLOv11Detection:
    def __init__(
        self, 
        model_path=cfg["model"]["detection"]["yolov11"]["pt"]["model_path"]["pt"],
        confidence_threshold=cfg["model"]["detection"]["yolov11"]["pt"]["confidence_threshold"],
        device="cuda",
    ):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.device = device

    def inference(self, frame, target_classes=[0, 1]):
        with torch.no_grad():
            results = self.model.predict(frame, conf=self.confidence_threshold, device=self.device, verbose=False)

            if not results or not results[0].boxes:
                return []

            filtered_results = []
            for result in results[0].boxes.data:
                x1, y1, x2, y2, conf, class_id = result.tolist()

                if target_classes is None or int(class_id) in target_classes:
                    filtered_results.append({
                        "bbox": [x1, y1, x2, y2],
                        "conf": conf,
                        "cls": int(class_id),
                    })

            return filtered_results

    def draw_box(self, frame, results, color=(0, 255, 0)):
        for result in results:
            x1, y1, x2, y2 = map(int, result["bbox"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        return frame
