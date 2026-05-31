import cv2
import numpy as np
import os

def test_color_diff(path):
    print("=" * 60)
    print(f"Testing Color-Diff on: {os.path.basename(path)}")
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
    
    h, w, c = img.shape
    area = w * h
    
    b, g, r = cv2.split(img)
    
    # Calculate Red-minus-Green difference
    diff = cv2.subtract(r, g)
    
    # Threshold diff: if difference <= 60, it's non-red (foreground)
    _, thresh = cv2.threshold(diff, 60, 255, cv2.THRESH_BINARY_INV)
    
    # Clean up with a small morphological opening/closing
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} contours using r-g difference")
    
    for idx, cnt in enumerate(contours):
        cnt_area = cv2.contourArea(cnt)
        ratio = cnt_area / area
        if ratio > 0.005:
            x, y, cw, ch = cv2.boundingRect(cnt)
            print(f"  Contour {idx}: Area Ratio={ratio:.4f}, BBox=[x={x}, y={y}, w={cw}, h={ch}]")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_red = os.path.join(uploads_dir, "1779970974_download.jpg")

if os.path.exists(img_red):
    test_color_diff(img_red)
else:
    print(f"Not found: {img_red}")
