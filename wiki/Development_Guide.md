# Development Guide

Complete guide for setting up a local development environment, contributing to Project Iceberg, and debugging the system.

## Prerequisites

- **Python 3.9+** (3.11+ recommended)
- **Node.js 18+** (with npm or yarn)
- **CUDA 13.0** (or fall back to CPU-only PyTorch)
- **Git** for version control
- **FFmpeg** for media processing (optional, for local testing)

### Windows Setup

**Install Python and Node.js:**
```powershell
# Using Windows Package Manager (winget)
winget install Python.Python.3.11
winget install OpenJS.NodeJS
```

Or download from:
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/

**Verify installations:**
```powershell
python --version  # Should be 3.9+
node --version    # Should be 18+
npm --version     # Should be 8+
```

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/example/project-iceberg.git
cd project-iceberg
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

If you have CUDA 13.0 installed and want GPU acceleration:
```bash
# PyTorch with CUDA is already in requirements.txt
# Just verify GPU is available:
python -c "import torch; print(f'GPU available: {torch.cuda.is_available()}')"
```

### 4. Set Up Frontend

```bash
cd frontend
npm install
cd ..
```

### 5. Generate Cryptographic Keys (Optional)

For local testing, you can generate test keys:

```bash
python scripts/generate_keys.py
```

Keys are stored in `keys/` directory (excluded from version control).

### 6. Verify Setup

```bash
# Test Python imports
python -c "
import fastapi
import torch
import cv2
import faiss
print('✓ All Python dependencies installed')
"

# Test Node.js/npm
npm --version
echo "✓ Node.js environment ready"
```

---

## Running the Application

### Terminal Setup

Open 4 terminals and activate the Python environment in each:

```powershell
venv\Scripts\activate
```

### Terminal 1: Backend API Server

```bash
python server.py
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Backend is now listening on `http://localhost:8000`

### Terminal 2: Frontend Development Server

```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v8.0.10  ready in 123 ms

➜  Local:   http://localhost:5173/
```

Frontend is now accessible at `http://localhost:5173`

### Terminal 3: Crawler Worker

```bash
python engine.py --mode crawler
```

Expected output:
```
[Crawler] Starting feed polling...
[Crawler] Polling YouTube feeds...
[Crawler] Polling Twitch feeds...
...
```

### Terminal 4: Verifier Worker

```bash
python engine.py --mode verifier
```

Expected output:
```
[Verifier] Starting verification worker...
[Verifier] Waiting for tasks in queue...
```

### Access the Application

Open your browser to:
- **Frontend**: http://localhost:5173
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Common Development Tasks

### Adding a New API Endpoint

1. **Edit `server.py`:**

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/my-endpoint")
async def my_endpoint(payload: dict):
    """
    Description of what this endpoint does.
    
    Args:
        payload: Request data
    
    Returns:
        Response with results
    """
    try:
        # Your logic here
        result = process_data(payload)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Test the endpoint:**

```bash
curl -X POST http://localhost:8000/my-endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

3. **View auto-generated docs:**

Navigate to http://localhost:8000/docs and test interactively.

### Adding a New React Component

1. **Create component file** `frontend/src/MyComponent.jsx`:

```javascript
import React from 'react';

export function MyComponent({ title }) {
  return (
    <div className="component">
      <h2>{title}</h2>
      {/* Component JSX */}
    </div>
  );
}
```

2. **Import in `App.jsx`:**

```javascript
import { MyComponent } from './MyComponent';

function App() {
  return (
    <div>
      <MyComponent title="Example" />
    </div>
  );
}
```

3. **Style with CSS:**

Edit `src/App.css` or create `src/MyComponent.css`:

```css
.component {
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
```

### Modifying Watermark Algorithm

Core logic in `models/dct_watermark.py`:

```python
def embed_watermark(frame, payload):
    """Embed 32-bit watermark payload into DCT coefficients."""
    # Convert frame to DCT domain
    dct_coeffs = cv2.dct(frame.astype(np.float32))
    
    # Modify specific coefficients based on payload bits
    for i, bit in enumerate(bin(payload)[2:].zfill(32)):
        # Modify coefficient at position (i)
        if bit == '1':
            dct_coeffs[...][i] += WATERMARK_STRENGTH
    
    # Convert back to spatial domain
    watermarked = cv2.idct(dct_coeffs)
    return watermarked.astype(np.uint8)
```

### Testing Watermark Extraction

```bash
python -c "
from models.dct_watermark import embed_watermark, extract_payload
import cv2
import numpy as np

# Create test image
test_frame = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
payload = 12345678

# Embed watermark
watermarked = embed_watermark(test_frame, payload)

# Extract payload
extracted = extract_payload(watermarked)

print(f'Original:  {payload}')
print(f'Extracted: {extracted}')
print(f'Match: {payload == extracted}')
"
```

---

## Debugging

### Enable Debug Logging

Set environment variable before running:

```bash
# Windows PowerShell
$env:LOG_LEVEL = "DEBUG"
python server.py

# Windows Command Prompt
set LOG_LEVEL=DEBUG
python server.py
```

### Inspect Message Queue

```python
# In a Python console
import multiprocessing as mp
from engine import task_queue, result_queue

print(f"Task queue size: {task_queue.qsize()}")
print(f"Result queue size: {result_queue.qsize()}")
```

### Monitor Memory & CPU

```bash
# Windows: Use Task Manager or Resource Monitor
# macOS/Linux:
top -p $(pgrep -f "python server.py")
```

### Database/FAISS Index Issues

```bash
# Rebuild FAISS index
python -c "
from models.lstm_detector import rebuild_faiss_index
rebuild_faiss_index()
print('✓ FAISS index rebuilt')
"
```

### Browser Developer Tools

Open browser console (F12) to:
- Inspect SSE stream messages
- Check network requests
- Monitor React component state (install React DevTools extension)

---

## Testing

### Run Unit Tests

```bash
# If pytest is installed:
pytest tests/ -v

# Basic test without pytest:
python -m unittest discover -s tests -p "test_*.py"
```

### Manual Testing Checklist

- [ ] Upload test media via `/upload` endpoint
- [ ] Verify asset appears in `/assets` list
- [ ] Subscribe to SSE stream at `/verify-stream`
- [ ] Simulate piracy via `/simulate-piracy`
- [ ] Watch real-time alerts appear in SSE stream
- [ ] Check logs in `/logs` endpoint
- [ ] Test mock feeds (`/mock-feed/youtube`, `/mock-feed/twitch`)

### Load Testing

```bash
# Using Apache Bench (ab)
ab -n 1000 -c 10 http://localhost:8000/assets

# Using wrk (if installed)
wrk -t4 -c100 -d30s http://localhost:8000/assets
```

---

## Code Style

### Python

Follow **PEP 8** and use **Black** for formatting:

```bash
# Install Black
pip install black

# Format file
black server.py

# Check formatting without changing
black --check models/
```

### JavaScript/React

Use **ESLint** (already configured):

```bash
cd frontend
npm run lint

# Auto-fix issues
npm run lint -- --fix
```

### Docstring Convention

Python docstrings use Google style:

```python
def process_media(url: str, timeout: int = 30) -> dict:
    """Process media from URL and extract watermark.
    
    Args:
        url: Remote media URL or local file path
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with keys:
            - payload: Extracted 32-bit watermark
            - confidence: Float 0.0-1.0
            - frames_analyzed: Integer count
    
    Raises:
        ValueError: If URL is invalid
        TimeoutError: If request exceeds timeout
    """
    pass
```

---

## Git Workflow

### Before Starting Work

```bash
# Create feature branch
git checkout -b feature/my-feature

# Keep branch updated
git pull origin main
```

### During Development

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new verification endpoint

- Implement POST /verify-deep endpoint
- Add DCT watermark extraction
- Update API documentation"

# Push to remote
git push origin feature/my-feature
```

### Before Merging

```bash
# Rebase on main to keep history clean
git fetch origin
git rebase origin/main

# Resolve conflicts if any
# Then force push
git push origin feature/my-feature --force-with-lease
```

### Create Pull Request

Create PR with:
- Clear title: `feat: add new verification endpoint`
- Description of changes
- Screenshots (if UI changes)
- Related issue numbers (#123)

---

## Environment Variables

Create `.env` file in project root for local configuration:

```bash
# FastAPI
LOG_LEVEL=INFO
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=500

# Workers
CRAWLER_POLL_INTERVAL=5
VERIFIER_BATCH_SIZE=10
FAISS_INDEX_PATH=data/faiss_index

# Testing
MOCK_FEED_DELAY_SECONDS=2
SIMULATE_PIRACY_ENABLED=true
```

Load in Python:

```python
import os
from dotenv import load_dotenv

load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO")
upload_dir = os.getenv("UPLOAD_DIR", "uploads")
```

---

## Performance Profiling

### Profile Server Requests

```bash
pip install py-spy

py-spy record -o profile.svg -- python server.py
# Make requests, then Ctrl+C
# Open profile.svg in browser
```

### Memory Profiling

```bash
pip install memory-profiler

python -m memory_profiler models/dct_watermark.py
```

### Verifier Performance

```bash
python -c "
import time
from models.dct_watermark import extract_payload
import cv2

# Simulate frame processing
frames = [cv2.imread('test.jpg') for _ in range(100)]

start = time.time()
for frame in frames:
    extract_payload(frame)
elapsed = time.time() - start

print(f'Processed {len(frames)} frames in {elapsed:.2f}s')
print(f'Speed: {len(frames)/elapsed:.1f} fps')
"
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
venv\Scripts\activate  # Activate environment first!
pip install -r requirements.txt
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# Kill process or use different port
python server.py --port 8001
```

### Issue: GPU not detected by PyTorch

**Solution:**
```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.current_device())
print(torch.cuda.get_device_name(0))

# If False, reinstall PyTorch with CUDA:
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
```

### Issue: FAISS index corrupted

**Solution:**
```bash
# Delete and rebuild
rm data/faiss_index
python -c "from engine import rebuild_faiss_index; rebuild_faiss_index()"
```

### Issue: SSE connection drops

**Solution:**
- Check browser console for errors
- Verify backend is running (`http://localhost:8000/docs`)
- Firewall may be blocking connections
- Try `http://127.0.0.1:8000` instead of `localhost`

---

## Useful Commands Reference

```bash
# Activate environment
venv\Scripts\activate

# Run all 4 components
python server.py                   # Terminal 1
npm run dev -C frontend            # Terminal 2
python engine.py --mode crawler    # Terminal 3
python engine.py --mode verifier   # Terminal 4

# Test individual modules
python -m pytest tests/
python -c "from models.dct_watermark import test_watermark; test_watermark()"
python debug.py

# Format and lint code
black .
cd frontend && npm run lint

# Build for production
cd frontend && npm run build
```

---

See [Architecture](Architecture.md) for system design, [API Documentation](API_Documentation.md) for endpoints.
