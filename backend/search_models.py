import os

search_paths = [
    r"C:\Users\DEEPAK\.gemini",
    r"C:\Users\DEEPAK\Downloads",
    r"C:\Program Files"
]

print("Scanning for models...")
found = []
for base_path in search_paths:
    if not os.path.exists(base_path):
        continue
    for root, dirs, files in os.walk(base_path):
        # Limit depth to avoid scanning massive directories
        if root.count(os.sep) - base_path.count(os.sep) > 3:
            continue
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.onnx', '.weights', '.pb', '.xml']:
                # Filter out system XML files and focus on cascades or models
                if ext == '.xml' and 'cascade' not in file.lower() and 'haarcascade' not in file.lower():
                    continue
                full_path = os.path.join(root, file)
                found.append(full_path)
                print(f"Found: {full_path}")

print(f"Scan complete. Found {len(found)} candidate model/cascade files.")
