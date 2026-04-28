# API Documentation

Complete reference for all Project Iceberg REST API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication is implemented. In production, all endpoints should be protected with OAuth 2.0 or similar.

---

## Media Management

### Upload Reference Media

Upload a media file to be watermarked and registered for future verification.

```http
POST /upload
Content-Type: multipart/form-data

file: <binary media file>
metadata: {
  "title": "Official Broadcast",
  "source": "Sports Network",
  "broadcast_id": "2026-04-28-game-01"
}
```

**Response (200 OK):**
```json
{
  "asset_id": "a1b2c3d4e5f6g7h8",
  "filename": "broadcast_2026-04-28.mp4",
  "watermark_payload": 12345678,
  "watermark_strength": 0.95,
  "timestamp": "2026-04-28T14:32:15Z",
  "storage_path": "uploads/a1b2c3d4e5f6g7h8.mp4"
}
```

**Parameters:**
- `file` (required): Video file (MP4, MKV, or HLS manifest)
- `metadata` (optional): JSON object with custom fields

**Errors:**
- `400 Bad Request` — Missing file or invalid metadata
- `413 Payload Too Large` — File exceeds size limit (typically 500 MB)
- `415 Unsupported Media Type` — Invalid file format

---

### List Registered Assets

Retrieve all registered reference media.

```http
GET /assets?limit=50&offset=0
```

**Response (200 OK):**
```json
{
  "total": 156,
  "assets": [
    {
      "asset_id": "a1b2c3d4e5f6g7h8",
      "title": "Official Broadcast",
      "source": "Sports Network",
      "upload_timestamp": "2026-04-28T10:00:00Z",
      "watermark_payload": 12345678,
      "size_bytes": 524288000,
      "status": "active"
    },
    {
      "asset_id": "z9y8x7w6v5u4t3s2",
      "title": "Live Stream Replay",
      "source": "Archive",
      "upload_timestamp": "2026-04-27T18:30:00Z",
      "watermark_payload": 87654321,
      "size_bytes": 716800000,
      "status": "active"
    }
  ]
}
```

**Query Parameters:**
- `limit` (optional, default: 50): Max results per page
- `offset` (optional, default: 0): Pagination offset
- `status` (optional): Filter by status (active, archived, invalid)

---

### Get Asset Details

Retrieve detailed metadata for a specific asset.

```http
GET /assets/{asset_id}
```

**Response (200 OK):**
```json
{
  "asset_id": "a1b2c3d4e5f6g7h8",
  "title": "Official Broadcast",
  "source": "Sports Network",
  "broadcast_id": "2026-04-28-game-01",
  "upload_timestamp": "2026-04-28T10:00:00Z",
  "watermark_payload": 12345678,
  "watermark_strength": 0.95,
  "video_duration_seconds": 7200,
  "resolution": "1920x1080",
  "fps": 30,
  "codec": "h264",
  "faiss_vector_id": 1,
  "detections_count": 12,
  "last_detection": "2026-04-28T14:15:00Z"
}
```

**Errors:**
- `404 Not Found` — Asset does not exist

---

## Verification API

### Verify Media (Immediate Check)

Perform fast C2PA validation. For deep watermark analysis, use `/verify-stream` instead.

```http
POST /verify
Content-Type: application/json

{
  "url": "https://example.com/stream.m3u8",
  "source": "youtube",
  "fast_mode": true
}
```

**Response (200 OK):**
```json
{
  "verification_id": "v_12345678",
  "url": "https://example.com/stream.m3u8",
  "c2pa_status": "invalid",
  "c2pa_error": "Signature verification failed",
  "quick_verdict": "SUSPICIOUS",
  "queued_for_analysis": true,
  "timestamp": "2026-04-28T14:32:15Z"
}
```

**Parameters:**
- `url` (required): Media URL or file path
- `source` (required): Source platform (youtube, twitch, custom)
- `fast_mode` (optional, default: true): Skip DCT analysis in initial response

**Response Status:**
- `verification_id`: Unique reference for this check (use to poll results)
- `c2pa_status`: "valid" | "invalid" | "missing" | "error"
- `quick_verdict`: "AUTHENTIC" | "SUSPICIOUS" | "UNKNOWN"
- `queued_for_analysis`: Whether task was enqueued for deep verification

---

### Stream Verification Results (SSE)

Subscribe to real-time verification results using Server-Sent Events.

```http
GET /verify-stream?client_id=client_12345
```

**Response Stream (200 OK, text/event-stream):**
```
data: {"verification_id":"v_87654321","asset_id":"a1b2c3d4e5f6g7h8","match_confidence":0.98,"frames_analyzed":240,"timestamp":"2026-04-28T14:32:45Z","status":"PIRACY_DETECTED"}

data: {"verification_id":"v_87654321","status":"COMPLETE"}
```

**Server-Sent Events Format:**

Each event contains a JSON object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `verification_id` | string | Unique verification request ID |
| `status` | string | Event status: "PROCESSING" \| "MATCH_FOUND" \| "PIRACY_DETECTED" \| "COMPLETE" \| "ERROR" |
| `asset_id` | string | Matched reference asset ID (if match found) |
| `match_confidence` | float | Confidence score 0.0-1.0 (if match found) |
| `frames_analyzed` | int | Number of frames processed |
| `url` | string | The media URL being analyzed |
| `error` | string | Error message (if status="ERROR") |
| `timestamp` | ISO8601 | Server-generated timestamp |

**Connection Management:**
- Client should reconnect with `client_id` on disconnect
- Server caches results for 24 hours
- Multiple clients can connect simultaneously

**Example Client Code (JavaScript):**
```javascript
const eventSource = new EventSource('/verify-stream?client_id=my_client');

eventSource.onmessage = (event) => {
  const result = JSON.parse(event.data);
  
  if (result.status === 'PIRACY_DETECTED') {
    console.warn(`Piracy detected: ${result.asset_id} matched with ${result.match_confidence * 100}% confidence`);
  } else if (result.status === 'COMPLETE') {
    eventSource.close();
  }
};

eventSource.onerror = () => {
  console.error('SSE connection failed, reconnecting...');
  eventSource.close();
};
```

---

### Get Verification Logs

Retrieve historical verification records.

```http
GET /logs?limit=50&offset=0&status=PIRACY_DETECTED&asset_id=a1b2c3d4e5f6g7h8&days=7
```

**Response (200 OK):**
```json
{
  "total": 147,
  "logs": [
    {
      "log_id": "log_001",
      "verification_id": "v_87654321",
      "url": "https://pirate-stream.com/game",
      "source": "twitch",
      "status": "PIRACY_DETECTED",
      "asset_id": "a1b2c3d4e5f6g7h8",
      "match_confidence": 0.98,
      "c2pa_status": "missing",
      "frames_analyzed": 240,
      "timestamp": "2026-04-28T14:32:45Z",
      "verification_duration_seconds": 12.5
    },
    {
      "log_id": "log_002",
      "verification_id": "v_11111111",
      "url": "https://official-stream.com/game",
      "source": "youtube",
      "status": "AUTHENTIC",
      "c2pa_status": "valid",
      "timestamp": "2026-04-28T14:10:00Z",
      "verification_duration_seconds": 0.3
    }
  ]
}
```

**Query Parameters:**
- `limit` (optional, default: 50): Results per page
- `offset` (optional, default: 0): Pagination offset
- `status` (optional): Filter by status (PIRACY_DETECTED, AUTHENTIC, UNKNOWN, ERROR)
- `asset_id` (optional): Filter by matched asset
- `days` (optional, default: 30): Search window in days
- `source` (optional): Filter by source platform

---

## Testing & Simulation

### Simulate Piracy Detection

Inject a suspicious URL directly into the verification queue without crawling. Useful for testing the Verifier worker.

```http
POST /simulate-piracy
Content-Type: application/json

{
  "url": "https://example.com/suspicious-stream.m3u8",
  "source": "twitch",
  "asset_id": "a1b2c3d4e5f6g7h8"
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "task_98765432",
  "url": "https://example.com/suspicious-stream.m3u8",
  "status": "queued",
  "expected_asset_id": "a1b2c3d4e5f6g7h8",
  "queued_at": "2026-04-28T14:32:15Z"
}
```

**Description:**
This endpoint bypasses the Crawler worker and directly queues the URL for Verifier analysis. Useful for:
- Testing watermark extraction without waiting for feed crawling
- Verifying specific suspected URLs immediately
- Debugging verification pipeline

---

### Get Mock Feed (YouTube)

Retrieve simulated YouTube feed with injected suspicious streams.

```http
GET /mock-feed/youtube?limit=20
```

**Response (200 OK):**
```json
{
  "source": "youtube",
  "feed": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "[LIVE] Official Broadcast - Game 01",
      "channel": "Sports Network Official",
      "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "thumbnail": "https://...",
      "views": 125000,
      "upload_time": "2026-04-28T10:00:00Z",
      "c2pa_metadata": {
        "signed": true,
        "issuer": "sports.network.official"
      }
    },
    {
      "video_id": "XcQ9w4wgdQw",
      "title": "GAME REPLAY - Best Moments [HD]",
      "channel": "Sports Highlights",
      "url": "https://youtube.com/watch?v=XcQ9w4wgdQw",
      "thumbnail": "https://...",
      "views": 50000,
      "upload_time": "2026-04-28T14:00:00Z",
      "c2pa_metadata": {
        "signed": false,
        "error": "No signature found"
      }
    }
  ]
}
```

---

### Get Mock Feed (Twitch)

Retrieve simulated Twitch feed with live streams.

```http
GET /mock-feed/twitch?category=sports
```

**Response (200 OK):**
```json
{
  "source": "twitch",
  "streams": [
    {
      "stream_id": "123456789",
      "title": "LIVE: Championship Game",
      "channel": "official_sports",
      "viewers": 45000,
      "is_live": true,
      "stream_url": "https://twitch.tv/official_sports",
      "hls_manifest": "https://usher.ttvnw.net/api/channel/hls/...",
      "c2pa_metadata": {
        "signed": true,
        "issuer": "twitch.official"
      }
    },
    {
      "stream_id": "987654321",
      "title": "Watch Party - Game Replay",
      "channel": "random_viewer",
      "viewers": 2,
      "is_live": true,
      "stream_url": "https://twitch.tv/random_viewer",
      "hls_manifest": "https://usher.ttvnw.net/api/channel/hls/...",
      "c2pa_metadata": {
        "signed": false,
        "error": "No credentials provided"
      }
    }
  ]
}
```

---

## Alert Webhook

### Post Piracy Alert

The Verifier worker POSTs alerts to this endpoint when piracy is detected.

```http
POST /alert
Content-Type: application/json

{
  "asset_id": "a1b2c3d4e5f6g7h8",
  "url": "https://pirate-stream.com/game",
  "confidence": 0.98,
  "frames_analyzed": 240,
  "watermark_payload": 12345678,
  "timestamp": "2026-04-28T14:32:45Z"
}
```

**Response (200 OK):**
```json
{
  "alert_id": "alert_12345",
  "received_at": "2026-04-28T14:32:45Z",
  "status": "processed"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error code",
  "message": "Human-readable error description",
  "details": {
    "field": "Additional context"
  }
}
```

### Common Errors

| HTTP Status | Error Code | Description |
|------------|-----------|-------------|
| 400 | INVALID_REQUEST | Malformed JSON or missing required fields |
| 400 | FILE_TOO_LARGE | Upload exceeds size limit |
| 401 | UNAUTHORIZED | Missing or invalid authentication token |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource does not exist |
| 429 | RATE_LIMIT | Too many requests from this IP/client |
| 500 | INTERNAL_ERROR | Server error during processing |
| 503 | SERVICE_UNAVAILABLE | Verifier workers offline or queue full |

---

## Rate Limiting

- **Anonymous clients:** 100 requests/hour per IP
- **Authenticated clients:** 1000 requests/hour per API key
- **SSE connections:** 10 simultaneous connections per client_id
- **Upload limit:** 500 MB per file, 50 GB per day per IP

---

## Pagination

All list endpoints support cursor-based pagination:

```
GET /assets?limit=50&offset=100
```

**Response:**
```json
{
  "total": 1000,
  "limit": 50,
  "offset": 100,
  "assets": [...]
}
```

Calculate next offset: `offset + limit`

---

## Examples

### Complete Verification Workflow

```bash
# 1. Upload reference media
curl -X POST http://localhost:8000/upload \
  -F "file=@broadcast.mp4" \
  -F 'metadata={"title":"Official Game","source":"Sports Network"}'

# Response: asset_id = "a1b2c3d4e5f6g7h8"

# 2. In another terminal, subscribe to real-time results
curl -N http://localhost:8000/verify-stream?client_id=test_client

# 3. Simulate piracy detection
curl -X POST http://localhost:8000/simulate-piracy \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://pirate-stream.example.com/game",
    "source": "twitch",
    "asset_id": "a1b2c3d4e5f6g7h8"
  }'

# 4. Watch SSE stream receive real-time alerts!
```

---

See [Architecture](Architecture.md) for system design details.
