import cv2
import numpy as np
import os

def inspect_pixels(path):
    print("=" * 60)
    print(f"Inspecting pixel values on: {os.path.basename(path)}")
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
        
    h, w, c = img.shape
    print(f"Image dimensions: {w}x{h}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Face region (approx x=120 to 180, y=50 to 120)
    face_roi = gray[50:120, 120:180]
    print(f"Face Grayscale: Min={np.min(face_roi)}, Max={np.max(face_roi)}, Avg={np.mean(face_roi):.1f}")
    
    # 2. Back rifle pile region (approx x=350 to 480, y=200 to 380)
    back_roi = gray[200:380, 350:480]
    print(f"Back Rifles Grayscale: Min={np.min(back_roi)}, Max={np.max(back_roi)}, Avg={np.mean(back_roi):.1f}")
    
    # 3. Hand rifle region (approx x=50 to 250, y=150 to 220)
    hand_roi = gray[150:220, 50:250]
    print(f"Hand Rifle Grayscale: Min={np.min(hand_roi)}, Max={np.max(hand_roi)}, Avg={np.mean(hand_roi):.1f}")
    
    # 4. Runway/sky background region (approx x=50 to 200, y=300 to 400)
    runway_roi = gray[300:400, 50:200]
    print(f"Runway Grayscale: Min={np.min(runway_roi)}, Max={np.max(runway_roi)}, Avg={np.mean(runway_roi):.1f}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
if os.path.exists(img_soldier):
    inspect_pixels(img_soldier)
else:
    print(f"Not found: {img_soldier}")
