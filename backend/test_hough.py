import cv2
import numpy as np
import os

def test_lines(path):
    print("=" * 60)
    print(f"Testing lines on: {os.path.basename(path)}")
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
    
    h, w, c = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Canny edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # 2. Hough Line Transform to detect straight line segments (like barrels, magazines, stocks)
    # minLineLength=50, maxLineGap=10
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=40, maxLineGap=10)
    
    line_count = len(lines) if lines is not None else 0
    print(f"Found {line_count} straight line segments")
    
    # Let's count long straight lines (length > 80 pixels)
    long_lines = 0
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if dist > 80:
                long_lines += 1
    print(f"Found {long_lines} long straight lines (> 80px)")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
img_red = os.path.join(uploads_dir, "1779970974_download.jpg")
img_man = os.path.join(uploads_dir, "1779971052_images.jpg")

for path in [img_soldier, img_red, img_man]:
    if os.path.exists(path):
        test_lines(path)
    else:
        print(f"Not found: {path}")
