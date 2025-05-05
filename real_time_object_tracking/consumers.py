import json
import pandas as pd
import base64
import asyncio
import cv2
import time
import numpy as np
import torch
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from ultralytics import YOLO
from .sort import Sort
from .coco_classes import class_names


class TrafficCounterConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Get the video path from session
        session = self.scope["session"]
        video_path = session.get("video_path")
        self.send(json.dumps({"Video": video_path}))
        if video_path:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                # Example: 1280
                cap.release()
            else:
                width = 800  # fallback
                height = 600
        else:
            width = 800  # fallback
            height = 600
        if not video_path:
            await self.close()
            return
        self.video_path = video_path
        self.all_data = []
        self.model_path = "yolov8n.pt"
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = YOLO(self.model_path).to(self.device)
        self.tracker = Sort()
        self.allowed_classes = {"car", "person", "bus", "train", "truck", "bicycle", "motorcycle"}
        self.crossed_objects = {}
        self.counts = {class_name: {"up": 0, "down": 0} for class_name in self.allowed_classes}
        # self.line_coords = [(0, 300), (800, 300)]  # Adjust as per requirement
        self.line_coords = [(0, int(session.get("line_y", 300))), (width, int(session.get("line_y", 300)))]
        self.running = True
        
        # Write CSV headers
        self.csv_path = "/Volumes/T7/PycharmProjects/Final_Project/yolov/real_time_object_tracking/media/Output_CSVs/results.csv"
        pd.DataFrame(columns=[
            "Frame_No", "ObjID", "x1", "y1", "x2", "y2", 
            "Class_Name", "Confidence", "Direction", "Aggregate_Count"
        ]).to_csv(self.csv_path, index=False)
        
        asyncio.create_task(self.process_video())

    async def disconnect(self, close_code):
        self.running = False
        raise StopConsumer()

    async def process_video(self):
        cap = cv2.VideoCapture(self.video_path)  # Use webcam (or provide video path)
        frame_number = 0
        prev_time = time.time()

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time + 1e-5)
            prev_time = curr_time
            
            processed_data, annotated_frame = self.process_frame(frame, frame_number, fps)
            self.all_data.extend(processed_data)
            # processed_data = self.process_frame(frame, frame_number)
            
            # # Draw bounding boxes on the frame
            # for obj in processed_data:
            #     x1, y1, x2, y2 = obj['bbox']
            #     label = f"{obj['class']} {obj['confidence']}"
            #     cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            #     cv2.putText(frame, label, (x1, y1 - 10),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # self.all_data.extend(processed_data)
            _, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            await self.send(json.dumps({
                "frame_data": processed_data,
                "frame_image": frame_base64,
            }))

            await asyncio.sleep(1 / 30)  # Maintain ~30 FPS

        cap.release()
        df = pd.DataFrame(self.all_data)
        # df.to_csv("/Volumes/T7/PycharmProjects/Final_Project/yolov/real_time_object_tracking/media/Output_CSVs/results.csv", index=False)
        df.to_csv(self.csv_path, index=False)

    def process_frame(self, frame, frame_number, fps):
        # results = self.model(frame)
        # detections = results[0].boxes.xyxy.cpu().numpy()
        # confidences = results[0].boxes.conf.cpu().numpy()
        # classes = results[0].boxes.cls.cpu().numpy()
        
        # dets = np.hstack((detections[:, :4], confidences.reshape(-1, 1)))
        # tracks = self.tracker.update(dets)
        # frame_data = []

        # for track in tracks:
        #     x1, y1, x2, y2, obj_id = map(int, track[:5])
        #     class_id = int(classes[np.argmax(confidences)])
        #     class_name = class_names[class_id] if class_id < len(class_names) else "Unknown"
        #     confidence = round(float(confidences[np.argmax(confidences)]), 2)

        #     if class_name not in self.allowed_classes:
        #         continue

        #     center_y = (y1 + y2) // 2
        #     line_y = self.line_coords[0][1]
        #     direction = None

        #     if obj_id not in self.crossed_objects:
        #         self.crossed_objects[obj_id] = center_y
        #     else:
        #         if self.crossed_objects[obj_id] < line_y <= center_y:
        #             direction = "down"
        #         elif self.crossed_objects[obj_id] > line_y >= center_y:
        #             direction = "up"

        #         if direction:
        #             self.counts[class_name][direction] += 1
        #             self.crossed_objects[obj_id] = center_y

        #     frame_data.append({
        #         "frame": frame_number,
        #         "object_id": obj_id,
        #         "bbox": [x1, y1, x2, y2],
        #         "class": class_name,
        #         "confidence": confidence,
        #         "direction": direction if direction else "N/A",
        #         "count": self.counts[class_name]
        #     })

        # return frame_data
        results = self.model(frame)
        detections = results[0].boxes.xyxy.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()

        dets = np.hstack((detections[:, :4], confidences.reshape(-1, 1)))
        tracks = self.tracker.update(dets)
        frame_data = []

        for track in tracks:
            x1, y1, x2, y2, obj_id = map(int, track[:5])

            best_match_idx = -1
            best_iou = 0
            for i, det in enumerate(detections):
                iou = self._iou(track[:4], det[:4])
                if iou > best_iou:
                    best_iou = iou
                    best_match_idx = i

            if best_match_idx != -1:
                class_id = int(classes[best_match_idx])
                class_name = class_names[class_id] if class_id < len(class_names) else "Unknown"
                confidence = round(float(confidences[best_match_idx]), 2)
            else:
                class_name = "Unknown"
                confidence = 0.0

            if class_name not in self.allowed_classes:
                continue

            center_y = (y1 + y2) // 2
            line_y = self.line_coords[0][1]
            direction = None

            if obj_id not in self.crossed_objects:
                self.crossed_objects[obj_id] = center_y
            else:
                if self.crossed_objects[obj_id] < line_y <= center_y:
                    direction = "down"
                elif self.crossed_objects[obj_id] > line_y >= center_y:
                    direction = "up"

                if direction:
                    self.counts[class_name][direction] += 1
                    self.crossed_objects[obj_id] = center_y

            aggregate_count = sum(sum(val.values()) for val in self.counts.values())
            frame_data.append({
                "Frame_No": frame_number,
                "ObjID": obj_id,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "Class_Name": class_name,
                "Confidence": confidence,
                "Direction": direction if direction else "N/A",
                "Aggregate_Count": aggregate_count,
            })

            # Draw bounding box and ID
            color = (0, 255, 0) if direction == "up" else (0, 0, 255) if direction == "down" else (255, 255, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{class_name} ID:{obj_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Draw user-defined line
        cv2.line(frame, self.line_coords[0], self.line_coords[1], (0, 255, 255), 3)

        # Display info (FPS + Class Counts)
        info_text = [f"FPS: {fps:.2f}"]
        for key, val in self.counts.items():
            info_text.append(f"{key}: Up-{val['up']} | Down-{val['down']}")

        for idx, text in enumerate(info_text):
            cv2.putText(frame, text, (10, 30 + (idx * 40)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        # Append to CSV immediately
        with open(self.csv_path, mode="a", newline="") as f:
            pd.DataFrame(frame_data).to_csv(f, header=False, index=False)

        return frame_data, frame

    def _iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
        return interArea / float(boxAArea + boxBArea - interArea)