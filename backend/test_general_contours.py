import cv2
import numpy as np
import os

def test_general(path):
    print("=" * 60)
    print(f"Testing general contours on: {os.path.basename(path)}")
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
    
    h, w = img.shape[:2]
    area = w * h
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Total contours: {len(contours)}")
    valid_count = 0
    for idx, cnt in enumerate(contours):
        cnt_area = cv2.contourArea(cnt)
        ratio = cnt_area / area
        if 0.005 < ratio < 0.6:
            x, y, cw, ch = cv2.boundingRect(cnt)
            aspect_ratio = float(cw) / ch
            if 0.15 < aspect_ratio < 6.0:
                print(f"Contour {idx}: BBox=[x={x}, y={y}, w={cw}, h={ch}], Area Ratio={ratio:.4f}, Aspect={aspect_ratio:.2f}")
                valid_count += 1
                
    print(f"Valid general contours: {valid_count}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
if os.path.exists(img_soldier):
    test_general(img_soldier)
else:
    print(f"Not found: {img_soldier}")
