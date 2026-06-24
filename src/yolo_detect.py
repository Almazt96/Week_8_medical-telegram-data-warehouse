# 4. Task 3: Data Enrichment with Object Detection (YOLO)
# To extract value from visual collateral attached to commerce channel entries, you run a lightweight YOLOv8 neural network inference iteration across downloaded files, generating diagnostic markers stored in structural tables.
# Object Detection Architecture Script:
# Computer Vision annotator
import os
import csv
from ultralytics import YOLO

def process_images_with_yolo():
    model = YOLO("yolov8n.pt")
    image_root = "data/raw/images"
    output_csv = "data/raw/csv/enrichment_detections.csv"
    
    records = []
    
    for root, dirs, files in os.walk(image_root):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                full_path = os.path.join(root, file)
                msg_id = os.path.splitext(file)[0]
                
                results = model(full_path, verbose=False)
                detected_labels = []
                confidence_scores = []
                
                for box in results[0].boxes:
                    cls_id = int(box.cls[0])
                    label = model.names[cls_id]
                    conf = float(box.conf[0])
                    detected_labels.append(label)
                    confidence_scores.append(conf)
                
                category = "other"
                if "person" in detected_labels and ("bottle" in detected_labels or "cup" in detected_labels):
                    category = "promotional"
                elif "bottle" in detected_labels or "container" in detected_labels:
                    category = "product_display"
                elif "person" in detected_labels:
                    category = "lifestyle"

                records.append({
                    "message_id": msg_id,
                    "detected_class": ",".join(detected_labels) if detected_labels else "none",
                    "confidence_score": max(confidence_scores) if confidence_scores else 0.0,
                    "image_category": category
                })

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["message_id", "detected_class", "confidence_score", "image_category"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Image semantic classification file generated successfully: {len(records)} media items processed.")

if __name__ == "__main__":
    process_images_with_yolo()