import cv2
import numpy as np
import os
import urllib.request

# MobileNet-SSD 21 classes (trained on Pascal VOC dataset)
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

def ensure_dnn_models_exist():
    """
    Ensures that the pre-trained Caffe MobileNet-SSD weights and configuration exist locally.
    Downloads them programmatically if missing, using robust mirror fallbacks.
    """
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    prototxt_path = os.path.join(models_dir, 'MobileNetSSD_deploy.prototxt')
    caffemodel_path = os.path.join(models_dir, 'MobileNetSSD_deploy.caffemodel')
    
    # Mirror sets
    prototxt_urls = [
        "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/voc/MobileNetSSD_deploy.prototxt",
        "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/dnn/MobileNetSSD_deploy.prototxt"
    ]
    
    caffemodel_urls = [
        "https://github.com/PINTO0309/MobileNet-SSD-RealSense/raw/master/caffemodel/MobileNetSSD/MobileNetSSD_deploy.caffemodel",
        "https://github.com/nikmart/pi-object-detection/raw/master/MobileNetSSD_deploy.caffemodel"
    ]
    
    # 1. Download Prototxt
    if not os.path.exists(prototxt_path):
        success = False
        for url in prototxt_urls:
            try:
                print(f"[DNN THREAT DETECTOR] Downloading architecture from {url}...")
                urllib.request.urlretrieve(url, prototxt_path)
                print("[DNN THREAT DETECTOR] Prototxt downloaded successfully.")
                success = True
                break
            except Exception as e:
                print(f"[DNN MIRROR FAILED] Prototxt download failed from {url}: {e}")
        if not success:
            return None, None, "Failed to download network architecture from all mirrors"
            
    # 2. Download Caffemodel
    if not os.path.exists(caffemodel_path):
        success = False
        for url in caffemodel_urls:
            try:
                print(f"[DNN THREAT DETECTOR] Downloading weights from {url} (approx. 23MB)...")
                urllib.request.urlretrieve(url, caffemodel_path)
                print("[DNN THREAT DETECTOR] Caffemodel downloaded successfully.")
                success = True
                break
            except Exception as e:
                print(f"[DNN MIRROR FAILED] Caffemodel download failed from {url}: {e}")
        if not success:
            return None, None, "Failed to download pre-trained weights from all mirrors"
            
    return prototxt_path, caffemodel_path, None

def run_dnn_object_detection(image_path, confidence_threshold=0.25):
    """
    Runs fully offline deep learning inference using MobileNet-SSD to detect 
    objects like persons, cars, trains (tanks), or aeroplanes in the scene.
    Returns detected regions of interest (ROIs) with labels.
    """
    detected_objects = []
    
    # 1. Ensure models exist
    prototxt, caffemodel, error = ensure_dnn_models_exist()
    if error or not prototxt or not caffemodel:
        print(f"[DNN INFERENCE SKIPPED] Model weights unavailable: {error}")
        return detected_objects
        
    try:
        # 2. Load the pre-trained Caffe network
        net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
        
        # 3. Read image and construct input blob
        img = cv2.imread(image_path)
        if img is None:
            return detected_objects
            
        h, w = img.shape[:2]
        
        # Pre-process image: resize to 300x300 and normalize mean values
        blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 0.007843, (300, 300), 127.5)
        net.setInput(blob)
        
        # 4. Perform forward pass (inference)
        detections = net.forward()
        
        # 5. Parse detections
        # detections shape is [1, 1, N, 7] where N is the number of candidate detections
        num_detections = detections.shape[2]
        for i in range(num_detections):
            confidence = detections[0, 0, i, 2]
            
            # Filter out weak detections
            if confidence > confidence_threshold:
                class_idx = int(detections[0, 0, i, 1])
                class_label = CLASSES[class_idx]
                
                # Scale coordinates back to original image size
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Bounds check
                startX = max(0, startX)
                startY = max(0, startY)
                endX = min(w - 1, endX)
                endY = min(h - 1, endY)
                
                cw = endX - startX
                ch = endY - startY
                
                if cw > 15 and ch > 15:
                    detected_objects.append({
                        'label': class_label.upper(),
                        'confidence': float(confidence),
                        'x': float(startX / w),
                        'y': float(startY / h),
                        'w': float(cw / w),
                        'h': float(ch / h)
                    })
                    print(f"[DNN DETECTED] {class_label.upper()} with {confidence*100:.1f}% confidence at bbox [{startX}, {startY}, {cw}, {ch}]")
                    
    except Exception as e:
        print(f"[DNN INFERENCE ERROR] Failed to run forward pass: {e}")
        
    return detected_objects
