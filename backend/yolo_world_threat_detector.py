import os
import cv2
import numpy as np

# Default classes to set for open-vocabulary YOLO-World
DEFAULT_CLASSES = ["handgun", "rifle", "knife", "weapon", "firearm", "pistol", "revolver"]

def run_yolo_world_detection(image_path, confidence_threshold=0.20):
    """
    Runs YOLO-World object detection locally using the ultralytics library.
    Sets classes dynamically to locate weapon threats, and outputs bounding boxes.
    Graciously falls back to empty list if ultralytics is not installed or fails.
    """
    detected_objects = []
    
    try:
        from ultralytics import YOLOWorld
    except BaseException as e:
        print(f"[YOLO-WORLD SKIPPED] Failed to import ultralytics or load dependencies (e.g. DLL/AVX2 support missing): {e}")
        return detected_objects
        
    try:
        # Load the smallest, most memory-efficient model (nano version, ~22MB)
        # It downloads programmatically on first run to backend/models/yolov8n-world.pt
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, 'yolov8n-world.pt')
        
        # Load the model
        model = YOLOWorld(model_path)
        
        # Set classes dynamically for open-vocabulary detection
        model.set_classes(DEFAULT_CLASSES)
        
        # Read the image to obtain dimensions
        img = cv2.imread(image_path)
        if img is None:
            return detected_objects
        h, w = img.shape[:2]
        
        # Run inference in evaluation mode
        # verbose=False reduces terminal logging
        results = model.predict(image_path, conf=confidence_threshold, verbose=False)
        
        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes
            
            for box in boxes:
                # Get coordinates, confidence, and class ID
                # xyxy is [x1, y1, x2, y2]
                xyxy = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls_idx = int(box.cls[0].cpu().numpy())
                
                label = DEFAULT_CLASSES[cls_idx] if cls_idx < len(DEFAULT_CLASSES) else "THREAT"
                
                startX, startY, endX, endY = xyxy
                startX = max(0, startX)
                startY = max(0, startY)
                endX = min(w - 1, endX)
                endY = min(h - 1, endY)
                
                cw = endX - startX
                ch = endY - startY
                
                if cw > 10 and ch > 10:
                    detected_objects.append({
                        'label': 'WEAPON/HAZARD REDACTED',
                        'confidence': conf,
                        'x': float(startX / w),
                        'y': float(startY / h),
                        'w': float(cw / w),
                        'h': float(ch / h)
                    })
                    print(f"[YOLO-WORLD DETECTED] {label.upper()} with {conf*100:.1f}% confidence at bbox [{int(startX)}, {int(startY)}, {int(cw)}, {int(ch)}]")
                    
    except Exception as e:
        print(f"[YOLO-WORLD INFERENCE ERROR] Failed to run detection: {e}")
        
    return detected_objects
