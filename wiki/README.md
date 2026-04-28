# Project Iceberg Wiki

Comprehensive documentation for the Project Iceberg media authentication and piracy detection system.

## 📚 Documentation Index

### Getting Started
- **[README](../README.md)** — Project overview, quick start, and feature highlights

### Core Documentation

1. **[System Architecture](Architecture.md)** — Deep dive into system design
   - Component interactions and data flow
   - Scalability patterns
   - Security architecture
   - Failure modes and recovery

2. **[API Documentation](API_Documentation.md)** — Complete REST API reference
   - All endpoints with request/response examples
   - Authentication and rate limiting
   - Error handling
   - Example workflows

3. **[Development Guide](Development_Guide.md)** — Local setup and contribution guide
   - Environment setup (Python, Node.js)
   - Running all components
   - Common development tasks
   - Debugging techniques
   - Git workflow
   - Testing procedures

4. **[DCT Watermarking Algorithm](Watermarking_Algorithm.md)** — Technical deep-dive
   - Mathematical foundation
   - Embedding algorithm
   - Extraction algorithm
   - Robustness analysis
   - Python implementation
   - Comparison with alternatives

5. **[Deployment Guide](Deployment_Guide.md)** — Production deployment
   - Docker/Docker Compose setup
   - Cloud deployment (AWS, GCP, Azure)
   - Horizontal scaling patterns
   - Security hardening
   - Monitoring and logging
   - Backup & disaster recovery

---

## 🎯 Quick Navigation by Role

### For Users
Start with [README](../README.md), then explore [API Documentation](API_Documentation.md) for integration.

### For Developers
1. [Development Guide](Development_Guide.md) — Get local environment running
2. [Architecture](Architecture.md) — Understand how components work
3. [DCT Watermarking Algorithm](Watermarking_Algorithm.md) — Deep technical understanding

### For DevOps/SRE
1. [Deployment Guide](Deployment_Guide.md) — Production setup
2. [Architecture](Architecture.md) — Scaling considerations
3. [API Documentation](API_Documentation.md) — Health checks and monitoring

### For Research/Academia
1. [DCT Watermarking Algorithm](Watermarking_Algorithm.md) — Detailed algorithm with math
2. [Architecture](Architecture.md) — System design and trade-offs
3. [README](../README.md) — Project motivation and goals

---

## 📋 Key Concepts

### Dual-Level Verification
Project Iceberg uses a two-pass verification approach:
1. **Level 1: C2PA Validation** — Fast cryptographic signature check
2. **Level 2: DCT Watermark Extraction** — Deep algorithmic analysis for stripped content

### Architecture Pattern
- **Event-driven:** Producer (Crawler) → Message Queue → Consumer (Verifier)
- **Real-time streaming:** Server-Sent Events (SSE) for live dashboard updates
- **Scalable:** Horizontally scale workers independent of API server

### Security Model
- Watermarks are deterministic (anyone can extract if they know the algorithm)
- Security through C2PA signatures and cryptographic validation
- Defense-in-depth with multiple verification levels

---

## 🚀 Getting Started

### Five-Minute Setup
```bash
# 1. Install dependencies
python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Run components (in separate terminals)
python server.py                    # Terminal 1: Backend
npm run dev -C frontend            # Terminal 2: Frontend
python engine.py --mode crawler    # Terminal 3: Crawler
python engine.py --mode verifier   # Terminal 4: Verifier

# 3. Open browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

See [Development Guide](Development_Guide.md) for detailed setup.

### Test the System
```bash
# Upload reference media
curl -X POST http://localhost:8000/upload \
  -F "file=@sample_video.mp4"

# Simulate piracy detection
curl -X POST http://localhost:8000/simulate-piracy \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/stream","source":"twitch"}'

# Watch real-time alerts
curl -N http://localhost:8000/verify-stream?client_id=test
```

---

## 🔧 Common Tasks

| Task | Resource |
|------|----------|
| Add new API endpoint | [Development Guide](Development_Guide.md#adding-a-new-api-endpoint) |
| Deploy to production | [Deployment Guide](Deployment_Guide.md) |
| Debug watermark extraction | [Watermarking Algorithm](Watermarking_Algorithm.md#implementation-in-python) |
| Scale to multiple workers | [Architecture](Architecture.md#horizontal-scaling) |
| Troubleshoot issues | [Development Guide](Development_Guide.md#troubleshooting) |
| Understand system flow | [Architecture](Architecture.md#data-flow-sequences) |

---

## 📊 System Overview

```
┌─────────────────────────────────────────────────────┐
│              Project Iceberg v3.1                    │
│                                                     │
│  Dual-Level Media Authentication & Piracy Detection │
└─────────────────────────────────────────────────────┘

                        Features
┌─────────────────────┬───────────────────────┐
│  C2PA Validation    │  DCT Watermarking     │
├─────────────────────┼───────────────────────┤
│ • Fast              │ • Compression-proof   │
│ • Cryptographic     │ • Invisible           │
│ • Signature-based   │ • Deterministic       │
└─────────────────────┴───────────────────────┘

                   Technology Stack
┌──────────────────────────────────────────┐
│ Backend: FastAPI, PyTorch, OpenCV, FAISS │
│ Frontend: React, Vite, Framer Motion     │
│ Messaging: Multiprocessing (or Redis)    │
│ Deployment: Docker, AWS/GCP/Azure        │
└──────────────────────────────────────────┘
```

---

## 🧠 Key Technologies

### Backend
- **FastAPI** — High-performance async API framework
- **PyTorch** — Deep learning for model inference
- **OpenCV** — Computer vision and media processing
- **FAISS** — Vector similarity search at scale

### Frontend
- **React 19** — Modern component-based UI
- **Vite** — Lightning-fast build tool
- **Server-Sent Events** — Real-time dashboard updates

### Media
- **DCT (Discrete Cosine Transform)** — Watermark embedding/extraction
- **C2PA** — Cryptographic metadata authentication
- **HLS/DASH** — Streaming protocol support

---

## 🔒 Security & Privacy

- **No personal data** — System verifies media, not users
- **Open-source algorithm** — DCT watermarking is transparent
- **Cryptographic validation** — C2PA provides trust anchors
- **Rate limiting** — Prevents API abuse
- **Authentication** — API key support (implement before production)

---

## 📈 Performance Characteristics

| Metric | Value |
|--------|-------|
| C2PA Validation | < 100 ms per stream |
| DCT Extraction | 2-5 fps on CPU, 30+ fps on GPU |
| Watermark Capacity | 32 bits per frame |
| False Positive Rate | < 1% |
| Compression Survival | 95%+ at MP4 10 Mbps |

---

## 🐛 Troubleshooting

**Issue:** Components not communicating?
- Check [Architecture](Architecture.md#failure-modes--recovery) for timeout settings
- See [Development Guide](Development_Guide.md#troubleshooting) for debugging

**Issue:** Watermark not extracting?
- Review [Watermarking Algorithm](Watermarking_Algorithm.md#robustness-analysis) for compression limits
- Test with [Python snippet](Watermarking_Algorithm.md#complete-watermark-embedding)

**Issue:** Production deployment failing?
- Follow [Deployment Guide](Deployment_Guide.md) step-by-step
- Check [Docker setup](Deployment_Guide.md#local-docker-setup)

---

## 📖 Reading Paths

**Path 1: Quick Overview** (15 minutes)
1. [README](../README.md) — Understand the problem and solution
2. [Architecture](Architecture.md) — Visualize the system

**Path 2: Integration** (1 hour)
1. [API Documentation](API_Documentation.md) — Learn endpoints
2. [Development Guide](Development_Guide.md#running-the-application) — Run locally
3. Test endpoints interactively

**Path 3: Deep Technical** (3 hours)
1. [Architecture](Architecture.md) — Full system design
2. [DCT Watermarking Algorithm](Watermarking_Algorithm.md) — Mathematical foundation
3. [Development Guide](Development_Guide.md) — Debug and modify

**Path 4: Production Ready** (2 hours)
1. [Deployment Guide](Deployment_Guide.md) — Deploy to cloud
2. [Development Guide](Development_Guide.md#environment-variables) — Configure securely
3. [Architecture](Architecture.md#monitoring--observability) — Set up monitoring

---

## 🤝 Contributing

Contributions welcome! See [Development Guide](Development_Guide.md#git-workflow) for:
- Code style guidelines
- Creating feature branches
- Pull request process
- Testing requirements

---

## 📞 Support

For questions or issues:
1. Check relevant section in wiki
2. Review [Troubleshooting](Development_Guide.md#troubleshooting)
3. Open issue with reproduction steps

---

## 📚 Additional Resources

- **Project Repository:** `d:\Projects\ProjectIceberg`
- **Technical Spec:** [SPEC.md](../SPEC.md)
- **Design System:** [DESIGN.md](../DESIGN.md)
- **API Base URL:** `http://localhost:8000` (development)
- **API Swagger Docs:** `http://localhost:8000/docs`

---

## 📄 Version & Updates

**Current Version:** 3.1  
**Last Updated:** April 2026  
**Status:** Active Development

---

**Start exploring:** Choose a link above based on your role and interests! 🚀
