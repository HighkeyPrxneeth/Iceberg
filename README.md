# Project Iceberg v3.1

**Dual-Level Verification Engine for Media Authentication & Piracy Detection**

Project Iceberg is a proof-of-concept platform designed to authenticate media (such as sports broadcasts) and track its unauthorized propagation in real time. It implements a sophisticated dual-level verification system combining cryptographic metadata validation and robust algorithmic watermarking to reliably detect piracy, even when content undergoes adversarial modifications like compression and metadata stripping.

## 🎯 Key Features

### Level 1: C2PA Metadata Authentication
- **Fast-path verification** using cryptographic signatures from official broadcast infrastructure
- Validates integrity of C2PA (Coalition for Content Provenance and Authenticity) metadata
- Saves computational resources by immediately recognizing authorized content
- Detects when signatures are deliberately stripped by pirates

### Level 2: DCT Watermarking Engine
- **Compression-proof steganography** embedded in media's frequency domain
- Block-based Discrete Cosine Transform (DCT) approach with 32-bit payload encoding
- Survives aggressive degradation including JPEG/MP4 compression and screen recording
- Invisible to human perception while maintaining robustness

## 📋 System Architecture

The platform is built as a distributed, horizontally-scalable system with five core components:

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  FastAPI    │◄────────│  Frontend    │────────►│  React SPA  │
│  Backend    │         │  Dashboard   │         │  (Vite)     │
└─────────────┘         └──────────────┘         └─────────────┘
      ▲                        ▲
      │ Real-time              │ SSE Stream
      │ Updates                │
      │                        │
┌─────┴──────────────────────────────────────┐
│     Multiprocessing Message Queues          │
└─────┬──────────────────┬───────────────────┘
      │                  │
      ▼                  ▼
┌────────────────┐  ┌──────────────────┐
│  Crawler       │  │  Verifier Worker │
│  Worker        │  │  (DCT Analysis)  │
└────────────────┘  └──────────────────┘
```

**Components:**

1. **API Server (FastAPI)**: Manages reference uploads, C2PA validation, mock social feeds, and real-time SSE updates
2. **Frontend Interface (React + Vite)**: Live verification log, asset dashboard, piracy simulation controls
3. **Message Queues**: Python multiprocessing for inter-component communication
4. **Crawler Worker**: Polls mock feeds (YouTube/Twitch clones), checks C2PA, queues suspicious URLs
5. **Verifier Worker**: Analyzes suspicious media using DCT watermark extraction

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI, Uvicorn, Python
- **Real-time Communication**: SSE-Starlette
- **Concurrency**: Python multiprocessing

### Frontend
- **Framework**: React 19+, Vite
- **Styling**: CSS with design system tokens
- **Routing**: React Router v7
- **Animations**: Framer Motion
- **Icons**: Lucide React

### Machine Learning & Vision
- **Deep Learning**: PyTorch with CUDA support
- **Computer Vision**: OpenCV (cv2)
- **Image Processing**: Pillow
- **Vector Search**: FAISS (CPU)

### Media & Cryptography
- **Video Processing**: FFmpeg
- **C2PA Utilities**: Standard library support
- **Media Streaming**: HLS manifest parsing

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- CUDA 13.0 (or CPU-only PyTorch)

### Installation

1. **Clone and navigate to project**
   ```bash
   cd d:\Projects\ProjectIceberg
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Generate cryptographic keys** (if needed)
   ```bash
   python scripts/generate_keys.py
   ```

### Running the System

**Start the FastAPI backend:**
```bash
python server.py
```
Backend runs at `http://localhost:8000`

**Start the frontend (development):**
```bash
cd frontend
npm run dev
```
Frontend runs at `http://localhost:5173`

**Run crawler worker** (in a separate terminal):
```bash
python engine.py --mode crawler
```

**Run verifier worker** (in another terminal):
```bash
python engine.py --mode verifier
```

## 📁 Project Structure

```
ProjectIceberg/
├── server.py                 # FastAPI backend entry point
├── engine.py                 # Worker process orchestration
├── check_alerts.py           # Alert processing
├── requirements.txt          # Python dependencies
│
├── frontend/                 # React + Vite SPA
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── Dashboard.jsx
│   │   ├── CloneTwitch.jsx   # Mock Twitch feed
│   │   ├── CloneYoutube.jsx  # Mock YouTube feed
│   │   └── assets/
│   ├── package.json
│   └── vite.config.js
│
├── models/                   # Machine learning modules
│   ├── lstm_detector.py      # LSTM-based detection
│   ├── dct_watermark.py      # DCT watermarking engine
│   ├── train_watermark.py    # Training pipeline
│   ├── vision_matcher.py     # Visual similarity matching
│   ├── watermark_2d.py       # 2D watermark operations
│   ├── c2pa_utils.py         # C2PA handling
│   └── weights/              # Model checkpoints
│
├── scripts/                  # Utilities
│   ├── generate_keys.py      # Cryptographic key generation
│   ├── check_cert.py         # Certificate validation
│   └── test_c2pa_minimal.py  # C2PA testing
│
├── data/                     # Persistent data
│   ├── lstm_detector.pt      # Pre-trained LSTM model
│   └── faiss_index/          # Vector search index
│
├── media/                    # Sample media for testing
│   ├── suspicious_stream/    # Mock HLS stream
│   └── *.txt                 # Test artifacts
│
├── uploads/                  # User-uploaded reference media
├── keys/                     # Cryptographic keys (sensitive)
└── SPEC.md & DESIGN.md       # Technical specifications
```

## 🔐 Security Notes

- **Keep `keys/` directory private** — never commit cryptographic keys
- **Upload directory** (`uploads/`) is not version controlled
- **Model weights** are large and stored in `data/` (use Git LFS if needed)
- Environment variables for API credentials should be in `.env` (not tracked)

## 🧪 Testing

### Check Alerts
```bash
python check_alerts.py
```

### Generate Mock Media
```bash
python generate_mock_media.py
```

### Debug Mode
```bash
python debug.py
```

### Test C2PA Validation
```bash
python scripts/test_c2pa_minimal.py
```

## 📊 API Overview

### Key Endpoints

**Authentication & Management**
- `POST /upload` — Upload reference media for watermarking
- `POST /register` — Register media metadata
- `GET /assets` — List registered assets

**Verification**
- `POST /verify` — Verify media authenticity
- `GET /verify-stream` — Stream verification results (SSE)
- `GET /logs` — Retrieve verification logs

**Simulation & Testing**
- `POST /simulate-piracy` — Inject suspicious URLs into verification queue
- `GET /mock-feed` — Retrieve mock YouTube/Twitch feeds

See [API Documentation](wiki/API_Documentation.md) for detailed endpoint reference.

## 📚 Documentation

- [Architecture & Design](wiki/Architecture.md) — System design and component interactions
- [API Documentation](wiki/API_Documentation.md) — Full endpoint reference with examples
- [Development Guide](wiki/Development_Guide.md) — Local setup, contribution guidelines, debugging
- [DCT Watermarking Algorithm](wiki/Watermarking_Algorithm.md) — Technical deep-dive into the DCT approach
- [Deployment Guide](wiki/Deployment_Guide.md) — Production deployment and scaling

## 🤝 Contributing

Contributions are welcome! Please refer to the [Development Guide](wiki/Development_Guide.md) for:
- Code style guidelines
- Setting up development environment
- Running tests
- Submitting pull requests

## 📄 License

Project Iceberg is provided as-is for research and evaluation purposes.

## 👥 Contact & Support

For questions or issues, please refer to the documentation or open an issue in the project repository.

---

**Last Updated**: April 2026 | **Version**: 3.1
