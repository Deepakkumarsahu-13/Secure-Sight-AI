import cv2
import os

def test_perfect_blur(path, output_path):
    img = cv2.imread(path)
    if img is None:
        print("Failed to load image")
        return
        
    h, w, c = img.shape
    print(f"Image size: {w}x{h}")
    
    # 1. Bounding box for the rifle in his hands
    # x = 10, y = 150, w = 230, h = 120 (normalized: x=0.02, y=0.36, w=0.43, h=0.29)
    rx1, ry1, rw1, rh1 = 10, 150, 230, 120
    
    # 2. Bounding box for the pile of rifles on his back
    # x = 200, y = 80, w = 280, h = 339 (normalized: x=0.38, y=0.19, w=0.53, h=0.81)
    rx2, ry2, rw2, rh2 = 200, 80, 280, 339
    
    # Apply strong Gaussian blur to these regions
    roi1 = img[ry1:ry1+rh1, rx1:rx1+rw1]
    img[ry1:ry1+rh1, rx1:rx1+rw1] = cv2.GaussianBlur(roi1, (99, 99), 50)
    
    roi2 = img[ry2:ry2+rh2, rx2:rx2+rw2]
    img[ry2:ry2+rh2, rx2:rx2+rw2] = cv2.GaussianBlur(roi2, (99, 99), 50)
    
    cv2.imwrite(output_path, img)
    print(f"Saved perfect blurred image to: {output_path}")

uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
img_soldier = os.path.join(uploads_dir, "1780044919_v6ox2910i8te1.png")
output_soldier = os.path.join(uploads_dir, "perfect_blurred_soldier.png")

if os.path.exists(img_soldier):
    test_perfect_blur(img_soldier, output_soldier)
else:
    print(f"Not found: {img_soldier}")
