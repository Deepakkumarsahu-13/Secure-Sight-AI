# Use a highly stable official Python Bookworm image
FROM python:3.11-slim-bookworm

# Prevent apt configuration prompts from blocking the build
ENV DEBIAN_FRONTEND=noninteractive

# Install Tesseract OCR (headless opencv-python does not require libgl1/libglib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && apt-get clean \
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
