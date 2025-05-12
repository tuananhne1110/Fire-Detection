import cv2
import numpy as np
import onnxruntime
import time
from configs.loader import cfg
from modules.entities.detection.yolov8.onnx.utils import xywh2xyxy, draw_detections, multiclass_nms


class YOLOv11DetectionONNX:
    def __init__(
        self,
        model_path=cfg["model"]["detection"]["yolov8"]["fire"]["model_path"]["onnx"],
        confidence_threshold=cfg["model"]["detection"]["yolov8"]["confidence_threshold"],
        iou_threshold=cfg["model"]["detection"]["yolov8"]["iou_threshold"]
    ):
        self.conf = confidence_threshold
        self.iou = iou_threshold

        # Initialize model với provider đúng
        self.initialize_model(model_path)

    def __call__(self, image):
        return self.detect_objects(image)

    def initialize_model(self, path):
        self.session = onnxruntime.InferenceSession(
            path, providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        self.get_input_details()
        self.get_output_details()

    def detect_objects(self, image):
        input_tensor = self.preprocess(image)
        outputs = self.inference(input_tensor)
        detections = self.postprocess(outputs)

        self.detections = detections

        return detections

    def preprocess(self, image):
        # Get original image size
        self.img_height, self.img_width = image.shape[:2]
        cv2.imwrite("input.jpg", image)
        # Calculate scale to keep original aspect ratio
        scale = min(self.input_width / self.img_width, self.input_height / self.img_height)
        new_w = int(self.img_width * scale)
        new_h = int(self.img_height * scale)

        # Resize image according to the calculated scale
        resized = cv2.resize(image, (new_w, new_h))
        cv2.imwrite("output.jpg", resized)
        # Create canvas (background) with target size, usually black
        canvas = np.zeros((self.input_height, self.input_width, 3), dtype=np.uint8)

        # Calculate padding to paste resized image in the center of the canvas
        pad_x = (self.input_width - new_w) // 2
        pad_y = (self.input_height - new_h) // 2
        canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized

        # Convert color space from BGR to RGB
        input_img = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        
        # Normalize pixel values to [0, 1]
        input_img = input_img / 255.0
        
        # Convert from HWC to CHW
        input_img = input_img.transpose(2, 0, 1)
        
        # Add batch dimension and cast to float32
        input_tensor = input_img[np.newaxis, :, :, :].astype(np.float32)
        
        return input_tensor


    def inference(self, input_data):
        # if input_data is raw image (uint8) then call preprocess to convert
        if isinstance(input_data, np.ndarray) and input_data.dtype == np.uint8 and input_data.ndim == 3:
            input_tensor = self.preprocess(input_data)
        else:
            input_tensor = input_data

        start = time.perf_counter()
        outputs = self.session.run(self.output_names, {self.input_names[0]: input_tensor})
        # print(f"Inference time: {(time.perf_counter() - start)*1000:.2f} ms")
        return outputs

    def postprocess(self, output):
        predictions = np.squeeze(output[0]).T  # convert to shape [num_predictions, 4+num_classes]

        scores = np.max(predictions[:, 4:], axis=1)
        mask = scores > self.conf
        predictions = predictions[mask, :]
        scores = scores[mask]

        if len(scores) == 0:
            return []

        class_ids = np.argmax(predictions[:, 4:], axis=1)
        boxes = self.extract_boxes(predictions)

        # Apply NMS to filter duplicate box
        indices = multiclass_nms(boxes, scores, class_ids, self.iou)

        results = []
        for i in indices:
            results.append({
                "bbox": boxes[i].tolist(),      
                "conf": float(scores[i]),         
                "cls": int(class_ids[i])         
            })
        return results

    def extract_boxes(self, predictions):
        # Get boxes from predictions
        boxes = predictions[:, :4]
        boxes = self.rescale_boxes(boxes)
        boxes = xywh2xyxy(boxes)
        return boxes

    def rescale_boxes(self, boxes):
        input_shape = np.array([self.input_width, self.input_height, self.input_width, self.input_height])
        boxes = np.divide(boxes, input_shape, dtype=np.float32)
        boxes *= np.array([self.img_width, self.img_height, self.img_width, self.img_height])
        return boxes

    def draw_detections(self, image, draw_scores=True, mask_alpha=0.4):
        return draw_detections(image, self.detections, None, None, mask_alpha)

    def get_input_details(self):
        model_inputs = self.session.get_inputs()
        self.input_names = [model_inputs[i].name for i in range(len(model_inputs))]
        self.input_shape = model_inputs[0].shape
        self.input_height = self.input_shape[2]
        self.input_width = self.input_shape[3]

    def get_output_details(self):
        model_outputs = self.session.get_outputs()
        self.output_names = [model_outputs[i].name for i in range(len(model_outputs))]
