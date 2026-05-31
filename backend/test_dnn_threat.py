import os
from dnn_threat_detector import run_dnn_object_detection

def test_dnn():
    print("=" * 60)
    print("TESTING OFFLINE PRE-TRAINED DNN MODEL ON SOLDIER PHOTO")
    print("=" * 60)
    
    uploads_dir = r"C:\Users\DEEPAK\.gemini\antigravity\scratch\privacy-guard-x\backend\uploads"
    filename = "1780044919_v6ox2910i8te1.png"
    img_path = os.path.join(uploads_dir, filename)
    
    if not os.path.exists(img_path):
        print(f"Error: Target image {img_path} not found")
        return
        
    # Run the offline DNN object detector
    detections = run_dnn_object_detection(img_path)
    
    print("\n[DNN DETECTION RESULTS]")
    print(f"Total objects detected: {len(detections)}")
    for idx, obj in enumerate(detections):
        print(f"  Object {idx}: Label='{obj['label']}', Confidence={obj['confidence']*100:.1f}%, BBox=[x={obj['x']:.3f}, y={obj['y']:.3f}, w={obj['w']:.3f}, h={obj['h']:.3f}]")

if __name__ == '__main__':
    test_dnn()
