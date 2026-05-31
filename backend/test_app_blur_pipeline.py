import os
import cv2
import numpy as np
from app import perform_ocr_offline_targeted, blur_with_ai_regions, load_settings

def test_full_pipeline():
    print("=" * 60)
    print("TESTING FULL OFFLINE REDACTION PIPELINE ON SOLDIER PHOTO")
    print("=" * 60)
    
    uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
    filename = "1780044919_v6ox2910i8te1.png"
    img_path = os.path.join(uploads_dir, filename)
    
    if not os.path.exists(img_path):
        print(f"Error: Target image {img_path} not found")
        return
        
    # 1. Run local OCR and straight-line density threat detector
    result = perform_ocr_offline_targeted(img_path)
    
    print("\n[PIPELINE RESULTS]")
    print(f"Is Sensitive:      {result['is_sensitive']}")
    print(f"Is Illegal:        {result['is_illegal']}")
    print(f"Illegal Type:      {result['illegal_type']}")
    print(f"Confidence Score:  {result['confidence_score']}")
    print(f"Document Type:     {result['document_type']}")
    print(f"Reason:            {result['reason']}")
    print(f"Detected Keywords: {result['detected_keywords']}")
    
    regions = result.get('regions', [])
    print(f"\nDetected {len(regions)} sensitive/threat regions:")
    for idx, reg in enumerate(regions):
        print(f"  Region {idx}: Label='{reg['label']}', x={reg['x']:.3f}, y={reg['y']:.3f}, w={reg['w']:.3f}, h={reg['h']:.3f}")
        
    if not regions:
        print("\nERROR: No regions were detected! Threat classification failed.")
        return
        
    # 2. Run Blur Engine
    settings = load_settings()
    # Ensure no watermark or banners
    settings['watermark'] = False
    
    blurred_file, err = blur_with_ai_regions(img_path, filename, regions, settings)
    if err:
        print(f"\nERROR: Blur engine failed: {err}")
    else:
        blurred_path = os.path.join(uploads_dir, blurred_file)
        print(f"\nSUCCESS! Redacted image saved to: {blurred_path}")
        
        # Verify the file exists and is valid
        if os.path.exists(blurred_path):
            img_out = cv2.imread(blurred_path)
            if img_out is not None:
                print(f"Verified output image dimensions: {img_out.shape[1]}x{img_out.shape[0]}")
            else:
                print("Error: Output image file is corrupted")
        else:
            print("Error: Output image file does not exist")

if __name__ == '__main__':
    test_full_pipeline()
