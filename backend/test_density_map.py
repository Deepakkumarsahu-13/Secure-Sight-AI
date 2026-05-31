import cv2
import numpy as np
import os

def test_line_density(path):
    print("=" * 60)
    print(f"Line density mapping on: {os.path.basename(path)}")
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
    
    h, w, c = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Canny edges and Hough lines
    edges = cv2.Canny(gray, 80, 200)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=40, maxLineGap=10)
    
    if lines is None:
        print("No lines detected")
        return
        
    print(f"Lines count: {len(lines)}")
    
    # 2. Accumulate lines on a blank float image
    accumulator = np.zeros((h, w), dtype=np.float32)
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # Draw line with value 1.0 and thickness 2
        cv2.line(accumulator, (x1, y1), (x2, y2), 1.0, 2)
        
    # 3. Apply a large Gaussian blur to smooth/cluster the densities
    # Using kernel size 51 or 75
    density_smooth = cv2.GaussianBlur(accumulator, (51, 51), 0)
    
    # Let's normalize it to 0-255 for analysis
    max_val = np.max(density_smooth)
    if max_val > 0:
        density_norm = (density_smooth / max_val * 255).astype(np.uint8)
    else:
        density_norm = np.zeros((h, w), dtype=np.uint8)
        
    # 4. Threshold the density map to find hot spots (highly dense line regions)
    # Let's try threshold values of 50, 80, 100
    for threshold_val in [40, 60, 80, 100]:
        _, thresh = cv2.threshold(density_norm, threshold_val, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"\nThreshold={threshold_val} -> Found {len(contours)} hot spots")
        
        for idx, cnt in enumerate(contours):
            cnt_area = cv2.contourArea(cnt)
            ratio = cnt_area / (w * h)
            x, y, cw, ch = cv2.boundingRect(cnt)
            print(f"  Hotspot {idx}: BBox=[x={x}, y={y}, w={cw}, h={ch}], Area Ratio={ratio:.4f}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
if os.path.exists(img_soldier):
    test_line_density(img_soldier)
else:
    print(f"Not found: {img_soldier}")
