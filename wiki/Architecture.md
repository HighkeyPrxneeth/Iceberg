# System Architecture & Design

## Overview

Project Iceberg is built as a **distributed, event-driven architecture** designed for horizontal scalability and real-time media verification. The system employs a producer-consumer pattern with asynchronous message passing to decouple verification workloads from the frontend API.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser / Client                          │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP + SSE
                   ▼
         ┌─────────────────────┐
         │   FastAPI Server    │
         │  (Port 8000)        │
         ├─────────────────────┤
         │ • Upload Handler    │
         │ • C2PA Validator    │
         │ • SSE Broadcaster   │
         │ • Alert Router      │
         └──────┬──────────────┘
                │
         ┌──────┴─────────────────────────┐
         │   Multiprocessing Queues       │
         │  (IPC Message Bus)             │
         ├────────────┬────────────────────┤
         │ Task Queue │ Result Queue       │
         └────┬───────┴────────┬───────────┘
              │                │
              ▼                ▼
         ┌──────────────┐  ┌──────────────┐
         │   Crawler    │  │   Verifier   │
         │   Worker     │  │   Worker     │
         ├──────────────┤  ├──────────────┤
         │ • Poll feeds │  │ • DCT extract│
         │ • Check C2PA │  │ • Match      │
         │ • Enqueue    │  │ • Alert      │
         └──────┬───────┘  └──────┬───────┘
                │                │
                └────┬───────────┘
                     │
                     ▼
            ┌────────────────────┐
            │  Persistent Data   │
            ├────────────────────┤
            │ • uploads/         │
            │ • data/faiss/      │
            │ • models/weights/  │
            └────────────────────┘
```

## Core Components

### 1. FastAPI Backend Server (`server.py`)

**Responsibilities:**
- HTTP API endpoint handling
- C2PA metadata validation
- Reference media ingestion & watermarking
- Real-time SSE streaming to connected clients
- Alert webhook integration

**Key Endpoints:**
- `POST /upload` — Accept and watermark reference media
- `POST /verify` — Immediate verification responses
- `GET /verify-stream` — Server-Sent Events for real-time log updates
- `GET /assets` — Asset inventory management
- `POST /simulate-piracy` — Test harness for queue injection

**Data Flow:**
1. Client uploads media → FastAPI receives and watermarks
2. Watermarked media stored in `uploads/`
3. Reference metadata indexed for rapid lookup
4. Verification requests immediately check C2PA, then queue deep analysis

### 2. Frontend Interface (`frontend/src/`)

**Tech Stack:**
- React 19 with Vite build system
- Server-Sent Events (SSE) for real-time updates
- React Router for navigation
- Framer Motion for smooth animations

**Key Components:**
- **Dashboard.jsx** — Main verification log and asset inventory
- **CloneTwitch.jsx** — Mock Twitch feed simulator with injectable pirated streams
- **CloneYoutube.jsx** — Mock YouTube feed simulator
- **App.jsx** — Routing and global state

**Real-time Updates:**
```javascript
const eventSource = new EventSource('/verify-stream');
eventSource.onmessage = (event) => {
  // Parse JSON verification result
  const alert = JSON.parse(event.data);
  // Update dashboard in real-time
  addToLog(alert);
};
```

### 3. Message Queue System (Python `multiprocessing.Queue`)

**Role:** Inter-process communication layer for worker coordination

**Queue Types:**
- **Task Queue** — Suspicious URLs and media needing verification
- **Result Queue** — Verification results (matched payload, confidence, metadata)
- **Alert Queue** — High-confidence piracy detections

**Benefits:**
- Decouples Crawler from Verifier (can scale independently)
- Persists work in memory for rapid processing
- Eliminates need for external message broker (RabbitMQ, Redis)
- Supports multiple producer/consumer patterns

### 4. Crawler Worker (`engine.py --mode crawler`)

**Responsibilities:**
- **Feed Polling:** Continuously samples mock YouTube/Twitch feeds
- **C2PA Pre-check:** Validates cryptographic signatures
- **URL Enqueueing:** Pushes suspicious (unauthenticated) media to task queue
- **Rate Limiting:** Respects API rate limits and backoff policies

**Algorithm:**
```python
while True:
    feeds = [fetch_youtube_feed(), fetch_twitch_feed()]
    for stream in feeds:
        try:
            # Level 1: Fast C2PA check
            if is_c2pa_valid(stream.metadata):
                continue  # Authorized, skip deep analysis
            # Level 1 failed: enqueue for deeper inspection
            task_queue.put({
                'url': stream.url,
                'source': stream.source,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Crawl error: {e}")
    time.sleep(POLL_INTERVAL)  # 5-10 seconds typical
```

### 5. Verifier Worker (`engine.py --mode verifier`)

**Responsibilities:**
- **Frame Extraction:** Decode suspicious media (MP4, HLS, etc.)
- **DCT Analysis:** Extract watermark payload from frequency domain
- **Payload Matching:** Compare extracted payload against registered assets
- **Alert Firing:** POST verified piracy alerts back to FastAPI

**Verification Pipeline:**
```python
while True:
    task = verifier_queue.get()
    try:
        # Extract frames from media (MP4, HLS stream segment)
        frames = extract_frames(task['url'], sample_rate=1)
        
        # DCT-based watermark extraction
        payloads = [extract_dct_payload(frame) for frame in frames]
        
        # Match against registered watermark database (FAISS index)
        matches = faiss_index.search(payloads, top_k=3)
        
        # If high-confidence match found, fire alert
        if matches.confidence > THRESHOLD:
            alert = {
                'asset_id': matches.asset_id,
                'url': task['url'],
                'confidence': matches.confidence,
                'timestamp': time.time()
            }
            requests.post('http://localhost:8000/alert', json=alert)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
```

## Data Flow Sequences

### Scenario 1: Reference Media Upload

```
Client
  │
  ├─ POST /upload (media file)
  │
  ▼
FastAPI Server
  ├─ Generate 32-bit payload
  ├─ Watermark with DCT algorithm
  ├─ Save to uploads/
  ├─ Index metadata in FAISS
  └─ Respond with asset_id
  │
  ▼
Database (data/faiss_index)
  └─ Store asset metadata + watermark vectors
```

### Scenario 2: Piracy Detection

```
Crawler Worker
  ├─ Poll YouTube/Twitch feeds
  ├─ Check C2PA signatures
  └─ Push suspicious URLs to task_queue
    │
    ▼
Verifier Worker
  ├─ Extract frames from URL/stream
  ├─ Run DCT watermark extraction
  ├─ Query FAISS index for matches
  └─ POST /alert to FastAPI
    │
    ▼
FastAPI Server
  ├─ Validate alert
  ├─ Store in verification log
  └─ Broadcast via SSE to all connected clients
    │
    ▼
Frontend (React)
  └─ Display new alert in real-time log
```

### Scenario 3: Simulation Mode

```
Client
  ├─ POST /simulate-piracy (mock URL)
  │
  ▼
FastAPI Server
  └─ Inject directly into task_queue
    │
    ▼
[Verifier Worker processes normally]
```

## Scalability Considerations

### Horizontal Scaling

**Current:** Single-machine multiprocessing

**To scale beyond single machine:**
1. Replace `multiprocessing.Queue` with Redis or RabbitMQ
2. Deploy multiple Verifier instances across nodes
3. Use load balancer (nginx) for FastAPI replicas
4. Centralize FAISS index or use distributed vector store

### Performance Optimizations

- **Frame sampling:** Verify only every Nth frame (e.g., 1 frame per second) instead of all
- **Batch processing:** Process multiple URLs in parallel within Verifier
- **Cached C2PA:** Pre-fetch and cache C2PA certs to avoid repeated API calls
- **Model quantization:** Use INT8 or FP16 for DCT operations to reduce memory/compute

## Security Architecture

### Trust Boundaries

```
┌──────────────────────────────────────────┐
│ Untrusted: User uploads, external URLs   │
│          (require full verification)     │
└──────────────────────────────────────────┘
           │
           ▼ Cryptographic validation (C2PA)
┌──────────────────────────────────────────┐
│ Semi-trusted: C2PA-signed content        │
│          (fast-path approval)            │
└──────────────────────────────────────────┘
           │
           ▼ Watermark extraction + matching
┌──────────────────────────────────────────┐
│ Trusted: Verified reference assets       │
│          (stored with cryptographic hash)|
└──────────────────────────────────────────┘
```

### Key Security Practices

1. **Cryptographic Keys:** Store in `keys/` directory, excluded from version control
2. **C2PA Validation:** Verify signatures against trusted root certificates
3. **Watermark Integrity:** Hash payloads to prevent tampering
4. **Access Control:** API should implement authentication (OAuth 2.0, etc.)
5. **Rate Limiting:** Prevent abuse of `/verify` and `/upload` endpoints

## Failure Modes & Recovery

| Component | Failure Mode | Recovery Strategy |
|-----------|--------------|-------------------|
| **Crawler** | Network timeout on feed | Exponential backoff, alert operator |
| **Verifier** | Out of memory (large video) | Stream frames instead of loading all |
| **FAISS Index** | Corrupted vectors | Rebuild from reference assets |
| **FastAPI** | Crash during alert broadcast | SSE reconnection + cached results |
| **Task Queue** | Lost messages on server crash | Implement persistent queue (DB-backed) |

## Monitoring & Observability

### Key Metrics

- **Crawler:** Feeds polled/sec, URLs enqueued/sec, error rate
- **Verifier:** Frames processed/sec, false positive rate, mean confidence score
- **API:** Request latency, SSE connection count, alert throughput
- **Resources:** CPU/GPU utilization, memory usage, queue depth

### Logging

All components log to stdout with structured JSON format:
```json
{
  "timestamp": "2026-04-28T14:32:15Z",
  "component": "verifier",
  "level": "INFO",
  "message": "Piracy detected",
  "asset_id": "a1b2c3d4",
  "confidence": 0.97
}
```

---

See [Development Guide](Development_Guide.md) for local architecture setup.
