import cv2
import numpy as np
import os

def test_segmentation(path):
    print("=" * 60)
    print(f"Testing segmentation on: {os.path.basename(path)}")
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
    
    h, w, c = img.shape
    area = w * h
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Method 1: Strict low-value thresholding (since gun is pure black, suit is dark, hand is light skin)
    # Let's try multiple thresholds: 30, 45, 60
    for t_val in [30, 45, 60]:
        _, thresh = cv2.threshold(gray, t_val, 255, cv2.THRESH_BINARY_INV)
        # Apply morphological opening to separate weakly connected components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh_clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(thresh_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"\n--- Strict Threshold at {t_val} ---")
        for idx, cnt in enumerate(contours):
            cnt_area = cv2.contourArea(cnt)
            ratio = cnt_area / area
            if 0.001 < ratio < 0.15:
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = float(cw) / ch
                if 0.3 < aspect_ratio < 3.0:
                    print(f"  Contour {idx}: Area Ratio={ratio:.4f}, BBox=[x={x}, y={y}, w={cw}, h={ch}], Aspect={aspect_ratio:.2f}")

    # Method 2: Canny Edge Detection
    edges = cv2.Canny(gray, 50, 150)
    kernel_edges = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated_edges = cv2.dilate(edges, kernel_edges)
    contours_canny, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print("\n--- Canny Edge + Dilation ---")
    for idx, cnt in enumerate(contours_canny):
        cnt_area = cv2.contourArea(cnt)
        ratio = cnt_area / area
        if 0.001 < ratio < 0.15:
            x, y, cw, ch = cv2.boundingRect(cnt)
            aspect_ratio = float(cw) / ch
            if 0.3 < aspect_ratio < 3.0:
                print(f"  Contour {idx}: Area Ratio={ratio:.4f}, BBox=[x={x}, y={y}, w={cw}, h={ch}], Aspect={aspect_ratio:.2f}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_man = os.path.join(uploads_dir, "1779971052_images.jpg")

if os.path.exists(img_man):
    test_segmentation(img_man)
else:
    print(f"Not found: {img_man}")
