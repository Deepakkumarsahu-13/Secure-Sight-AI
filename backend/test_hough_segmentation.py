import cv2
import numpy as np
import os

def segment_weapons(image_path):
    print("=" * 60)
    print(f"Segmenting weapons on: {os.path.basename(image_path)}")
    img = cv2.imread(image_path)
    if img is None:
        print("Failed to load image")
        return
    
    h, w, c = img.shape
    area = w * h
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Canny edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # 2. Hough Line Transform to detect straight line segments
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=40, maxLineGap=10)
    
    if lines is None:
        print("No lines detected")
        return []
    
    line_count = len(lines)
    print(f"Found {line_count} straight line segments")
    
    # Let's see the distribution of lines
    # We want to identify the bounding boxes of the weapons by grouping close-by/dense straight lines
    # We can create a mask of where the straight lines are, dialate it, and find contours.
    line_mask = np.zeros((h, w), dtype=np.uint8)
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # Draw the line on the mask with some thickness
        cv2.line(line_mask, (x1, y1), (x2, y2), 255, 15)
        
    # Dilate the line mask to merge nearby lines (e.g. adjacent guns or parts of the same gun)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 40))
    dilated_mask = cv2.dilate(line_mask, kernel)
    
    # Find contours on this mask
    contours, _ = cv2.findContours(dilated_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} line cluster contours")
    
    regions = []
    for idx, cnt in enumerate(contours):
        cnt_area = cv2.contourArea(cnt)
        ratio = cnt_area / area
        x, y, cw, ch = cv2.boundingRect(cnt)
        
        # We only want to blur where there is high line density (i.e. the gun pile and the hand gun)
        # We also want to make sure we don't blur the whole image (like a background cluster)
        # So we check:
        # 1. Bounding box area is not too huge (e.g. less than 50% of the image)
        # 2. The bounding box has a decent number of lines inside it
        # Let's count how many lines lie within this bounding box
        lines_inside = 0
        for line in lines:
            x1, y1, x2, y2 = line[0]
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            if x <= mx <= x + cw and y <= my <= y + ch:
                lines_inside += 1
                
        line_density = lines_inside / (cw * ch) if cw * ch > 0 else 0
        print(f"Cluster {idx}: BBox=[x={x}, y={y}, w={cw}, h={ch}], Area Ratio={ratio:.4f}, Lines Inside={lines_inside}")
        
        # If it has more than 10 lines and doesn't cover more than 60% of the image
        if lines_inside >= 8 and ratio < 0.6:
            # Let's do a bounding box refinement:
            # Within this bounding box, let's find the actual dark pixels (since weapons are dark)
            # or just use the bounding box of the lines themselves
            # Let's find the bounding box of the lines inside this cluster
            xs = []
            ys = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                if x <= mx <= x + cw and y <= my <= y + ch:
                    xs.extend([x1, x2])
                    ys.extend([y1, y2])
            if xs and ys:
                rx = min(xs)
                ry = min(ys)
                rw = max(xs) - rx
                rh = max(ys) - ry
                
                # Make sure the bounding box is valid
                if rw > 20 and rh > 20:
                    regions.append({
                        'label': 'WEAPON/HAZARD REDACTED',
                        'x': float(rx / w),
                        'y': float(ry / h),
                        'w': float(rw / w),
                        'h': float(rh / h)
                    })
                    print(f"  -> Added refined region: x={rx/w:.3f}, y={ry/h:.3f}, w={rw/w:.3f}, h={rh/h:.3f}")
                    
    return regions

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
if os.path.exists(img_soldier):
    segment_weapons(img_soldier)
else:
    print(f"Not found: {img_soldier}")
