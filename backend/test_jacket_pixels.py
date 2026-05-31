import cv2
import numpy as np
import os

def inspect_jacket(path):
    img = cv2.imread(path)
    if img is None:
        return
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Jacket region in the front (approx x=220 to 280, y=200 to 300)
    jacket_roi = gray[200:300, 220:280]
    print(f"Jacket Grayscale: Min={np.min(jacket_roi)}, Max={np.max(jacket_roi)}, Avg={np.mean(jacket_roi):.1f}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
inspect_jacket(img_soldier)
