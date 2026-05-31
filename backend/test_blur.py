import cv2
import numpy as np
import os

def detect_weapon_contours_offline(image_path):
    regions = []
    try:
        img = cv2.imread(image_path)
        if img is None:
            return regions

        h, w = img.shape[:2]
        area = w * h

        # 1. Check if the background is primarily red (like download.jpg)
        b, g, r = cv2.split(img)
        red_mask = (r > 130) & (g < 100) & (b < 100)
        red_ratio = np.sum(red_mask) / area

        # 2. Convert to grayscale and apply thresholding
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        if red_ratio > 0.25:
            # Red-minus-Green difference thresholding
            diff = cv2.subtract(r, g)
            _, thresh = cv2.threshold(diff, 70, 255, cv2.THRESH_BINARY_INV)
            
            # Morphological cleanup
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        else:
            # Otsu's thresholding segments foreground objects from background
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 3. Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            cnt_area = cv2.contourArea(cnt)
            ratio = cnt_area / area
            
            # Filter contours representing the weapon, ammo tray, or other illegal components.
            # They should be significant foreground objects (e.g. between 0.5% and 60% of image area).
            if 0.005 < ratio < 0.6:
                x, y, cw, ch = cv2.boundingRect(cnt)
                
                # Check aspect ratio to ensure it is not a thin line or extreme shape
                aspect_ratio = float(cw) / ch
                if 0.15 < aspect_ratio < 6.0:
                    regions.append({
                        'label': 'WEAPON/HAZARD REDACTED',
                        'x': float(x / w),
                        'y': float(y / h),
                        'w': float(cw / w),
                        'h': float(ch / h)
                    })
    except Exception as e:
        print(f"[OFFLINE WEAPON CONTOUR DETECTION FAILED] {e}")
    return regions

def apply_blur(image_path, regions, output_path):
    img = cv2.imread(image_path)
    if img is None:
        return
    h, w = img.shape[:2]
    
    for r in regions:
        rx = int(r['x'] * w)
        ry = int(r['y'] * h)
        rw = int(r['w'] * w)
        rh = int(r['h'] * h)
        
        # Bounds check
        rx = max(0, min(rx, w - 1))
        ry = max(0, min(ry, h - 1))
        rw = max(1, min(rw, w - rx))
        rh = max(1, min(rh, h - ry))
        
        roi = img[ry:ry+rh, rx:rx+rw]
        img[ry:ry+rh, rx:rx+rw] = cv2.GaussianBlur(roi, (99, 99), 50)
        cv2.rectangle(img, (rx, ry), (rx+rw, ry+rh), (0, 0, 220), 2)
        
    cv2.imwrite(output_path, img)
    print(f"Saved blurred image to {output_path}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_red = os.path.join(uploads_dir, "1779970974_download.jpg")
img_man = os.path.join(uploads_dir, "1779971052_images.jpg")

if os.path.exists(img_red):
    regions = detect_weapon_contours_offline(img_red)
    print(f"download.jpg found {len(regions)} regions:")
    for r in regions:
        print(f"  x={r['x']:.2f}, y={r['y']:.2f}, w={r['w']:.2f}, h={r['h']:.2f}")
    apply_blur(img_red, regions, os.path.join(uploads_dir, "test_blurred_download.jpg"))

if os.path.exists(img_man):
    regions = detect_weapon_contours_offline(img_man)
    print(f"images.jpg found {len(regions)} regions:")
    for r in regions:
        print(f"  x={r['x']:.2f}, y={r['y']:.2f}, w={r['w']:.2f}, h={r['h']:.2f}")
    apply_blur(img_man, regions, os.path.join(uploads_dir, "test_blurred_images.jpg"))
