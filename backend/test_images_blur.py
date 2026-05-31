import cv2
import numpy as np
import os

def test_man_blur(path, output_path):
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
    
    h, w, c = img.shape
    area = w * h
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Strict thresholding (gun is extremely dark, suit is dark, hand skin is bright)
    # This separates the gun from the suit because the bright hand acts as a natural separator!
    _, thresh = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY_INV)
    
    # 2. Morphological opening to disconnect any thin connections
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # 3. Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    blurred_count = 0
    for cnt in contours:
        cnt_area = cv2.contourArea(cnt)
        ratio = cnt_area / area
        
        # The handgun in a white-background photo covers between 0.1% and 5% of the image area.
        # The black suit covers >15% of the area.
        # This size-constraint perfectly isolates the gun and excludes the suit!
        if 0.001 < ratio < 0.05:
            x, y, cw, ch = cv2.boundingRect(cnt)
            aspect_ratio = float(cw) / ch
            
            # Check aspect ratio of a handgun (typically between 0.4 and 2.5)
            if 0.4 < aspect_ratio < 2.5:
                # Target blur on this bounding box
                roi = img[y:y+ch, x:x+cw]
                img[y:y+ch, x:x+cw] = cv2.GaussianBlur(roi, (51, 51), 30)
                cv2.rectangle(img, (x, y), (x+cw, y+ch), (0, 0, 220), 2)
                blurred_count += 1
                print(f"Blurred region: x={x}, y={y}, w={cw}, h={ch}, ratio={ratio:.4f}")
                
    cv2.imwrite(output_path, img)
    print(f"Saved test output to {output_path}. Blurred {blurred_count} regions.")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_man = os.path.join(uploads_dir, "1779971052_images.jpg")
output_man = os.path.join(uploads_dir, "test_blurred_man.jpg")

if os.path.exists(img_man):
    test_man_blur(img_man, output_man)
else:
    print(f"Not found: {img_man}")
