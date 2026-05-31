import cv2
import numpy as np
import os

def precision_blur(path):
    print("=" * 60)
    print(f"Testing precision blur on: {os.path.basename(path)}")
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
        cv2.line(accumulator, (x1, y1), (x2, y2), 1.0, 2)
        
    # 3. Apply a large Gaussian blur to smooth/cluster the densities
    density_smooth = cv2.GaussianBlur(accumulator, (51, 51), 0)
    
    # Normalize it to 0-255
    max_val = np.max(density_smooth)
    if max_val > 0:
        density_norm = (density_smooth / max_val * 255).astype(np.uint8)
    else:
        density_norm = np.zeros((h, w), dtype=np.uint8)
        
    # 4. Threshold the density map to find hot spots (highly dense line regions)
    # A threshold of 95-100 gives highly precise localization of complex straight lines (weapons)
    _, thresh = cv2.threshold(density_norm, 95, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Found {len(contours)} candidate hotspots")
    
    img_blurred = img.copy()
    regions = []
    
    for idx, cnt in enumerate(contours):
        cnt_area = cv2.contourArea(cnt)
        ratio = cnt_area / (w * h)
        x, y, cw, ch = cv2.boundingRect(cnt)
        
        # Filter out giant hotspots that cover the entire image or large background shapes
        # We only want to blur localized high-density straight line clusters (which are the weapons)
        if cw < 0.7 * w and ch < 0.7 * h and ratio < 0.25:
            # Expand the bounding box slightly for complete coverage of the weapon boundary
            expand_px = 15
            rx = max(0, x - expand_px)
            ry = max(0, y - expand_px)
            rw = min(w - rx, cw + 2 * expand_px)
            rh = min(h - ry, ch + 2 * expand_px)
            
            print(f"  Redacting Hotspot {idx}: BBox=[x={rx}, y={ry}, w={rw}, h={rh}], Ratio={ratio:.4f}")
            regions.append((rx, ry, rw, rh))
            
            # Apply a strong Gaussian blur to this region
            roi = img_blurred[ry:ry+rh, rx:rx+rw]
            img_blurred[ry:ry+rh, rx:rx+rw] = cv2.GaussianBlur(roi, (99, 99), 50)
            
    # Save the output to see if it's correct
    output_filename = "precision_blurred_" + os.path.basename(path)
    output_path = os.path.join(os.path.dirname(path), output_filename)
    cv2.imwrite(output_path, img_blurred)
    print(f"Saved redacted image to: {output_path}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
if os.path.exists(img_soldier):
    precision_blur(img_soldier)
else:
    print(f"Not found: {img_soldier}")
