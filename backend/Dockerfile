# Use a lightweight official Python image
FROM python:3.11-slim

# Install system dependencies (Tesseract OCR & OpenCV libraries)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir waitress # Production-grade web server for standard CPU execution

# Copy backend code
COPY . .

# Expose port and run Waitress
EXPOSE 5000
CMD ["python", "-c", "import os; from waitress import serve; from app import app; port = int(os.environ.get('PORT', 5000)); print(f'Waitress running on port {port}...'); serve(app, host='0.0.0.0', port=port)"]
