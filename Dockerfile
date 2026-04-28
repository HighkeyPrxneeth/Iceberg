FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies for OpenCV and FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Environment variables for default configuration
ENV LOG_LEVEL=INFO
ENV UPLOAD_DIR=/app/uploads
ENV FAISS_INDEX_PATH=/app/data/faiss_index

# The CMD will be overridden by docker-compose for workers
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
