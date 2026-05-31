import sys
import os

from app import perform_ocr_offline_targeted, blur_with_ai_regions

img_path = r'C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads\1780247311_german-tank.jpg'
res = perform_ocr_offline_targeted(img_path)
blurred_filename, error = blur_with_ai_regions(img_path, '1780247311_german-tank.jpg', res['regions'])
print("Blurred File:", blurred_filename)
print("Error:", error)
