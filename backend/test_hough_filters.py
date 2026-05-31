import cv2
import numpy as np
import os

def analyze_soldier_image(path):
    print("=" * 60)
    print(f"Analyzing soldier image: {os.path.basename(path)}")
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
    
    h, w, c = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Let's test different edge/Hough configurations
    for canny_low, canny_high in [(50, 150), (80, 200), (100, 250)]:
        edges = cv2.Canny(gray, canny_low, canny_high)
        for min_len, max_gap in [(30, 5), (40, 10), (50, 15)]:
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=min_len, maxLineGap=max_gap)
            num_lines = len(lines) if lines is not None else 0
            print(f"Canny({canny_low}, {canny_high}) | minLen={min_len}, maxGap={max_gap} => Lines: {num_lines}")

    # Let's use a standard configuration to find clusters: Canny(80, 200), minLen=40, maxGap=8
    edges = cv2.Canny(gray, 80, 200)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=40, maxLineGap=8)
    
    if lines is None:
        print("No lines detected in target configuration")
        return
        
    print(f"Target Configuration: Found {len(lines)} lines")
    
    # We want to group these lines into distinct visual clusters.
    # Let's draw lines on a blank image, but with a smaller thickness (e.g., 5 or 8) so that
    # the clusters don't all merge into one giant cluster covering the whole image.
    line_mask = np.zeros((h, w), dtype=np.uint8)
    for line in lines:
        x1, y1, x2, y2 = line[0]
        cv2.line(line_mask, (x1, y1), (x2, y2), 255, 6)
        
    # Apply morphological closing then opening to group nearby line segments
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    
    mask_processed = cv2.morphologyEx(line_mask, cv2.MORPH_CLOSE, kernel_close)
    mask_processed = cv2.morphologyEx(mask_processed, cv2.MORPH_OPEN, kernel_open)
    
    contours, _ = cv2.findContours(mask_processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} distinct clusters")
    
    for idx, cnt in enumerate(contours):
        cnt_area = cv2.contourArea(cnt)
        ratio = cnt_area / (w * h)
        x, y, cw, ch = cv2.boundingRect(cnt)
        
        # Calculate how many lines are within this contour's bounding box
        lines_inside = 0
        for line in lines:
            x1, y1, x2, y2 = line[0]
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            if x <= mx <= x + cw and y <= my <= y + ch:
                lines_inside += 1
                
        print(f"Cluster {idx}: BBox=[x={x}, y={y}, w={cw}, h={ch}], Area Ratio={ratio:.4f}, Lines={lines_inside}")
        
        # Let's check the line density (lines per unit area, or simply the percentage of line mask pixels)
        # An area with high line density represents complex rifle barrel/stock parts.
        roi_mask = line_mask[y:y+ch, x:x+cw]
        density = np.sum(roi_mask == 255) / (cw * ch) if cw * ch > 0 else 0
        print(f"  -> Pixel density of lines: {density:.3f}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
if os.path.exists(img_soldier):
    analyze_soldier_image(img_soldier)
else:
    print(f"Not found: {img_soldier}")
