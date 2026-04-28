import asyncio
import json
import os
import random
import time
import uuid
import shutil
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.dct_watermark import WatermarkEngine
from models.c2pa_utils import sign_file, validate_file

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

PORT = 8000

# ---------------------------------------------------------------------------
# Shared State
# ---------------------------------------------------------------------------

# Database of registered official assets
registered_files: list[dict] = []

# Mock database of posts on clone sites
clone_feeds = {
    "youtube": [],
    "twitch": []
}

# Alerts from the engine
alerts_database: list[dict] = []

sse_subscribers: list[asyncio.Queue] = []

# ---------------------------------------------------------------------------
# Helper: Broadcast
# ---------------------------------------------------------------------------

async def _broadcast_event(event_type: str, data: dict):
    message = {"type": event_type, "data": data}
    dead = []
    for q in sse_subscribers:
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        sse_subscribers.remove(q)

def _broadcast_sync(event_type: str, data: dict, loop):
    """Utility to broadcast from synchronous background threads"""
    asyncio.run_coroutine_threadsafe(_broadcast_event(event_type, data), loop)

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

watermark_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global watermark_engine
    print("[Server] Initializing Watermark Engine...")
    watermark_engine = WatermarkEngine()
    yield

app = FastAPI(title="Project Iceberg", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="frontend_assets")

# ---------------------------------------------------------------------------
# API: Dashboard Registration
# ---------------------------------------------------------------------------

def process_upload_task(temp_path: str, save_path: str, is_video: bool, entry: dict, payload, loop):
    def progress_cb(current, total):
        pct = int((current / total) * 100)
        _broadcast_sync("progress", {"id": entry["id"], "progress": pct}, loop)

    if is_video:
        watermark_engine.process_video(temp_path, save_path, payload, progress_cb)
    else:
        watermark_engine.process_image(temp_path, save_path, payload)
        progress_cb(1, 1)
        
    os.remove(temp_path)
    
    # Step 2: C2PA Signing
    c2pa_temp = os.path.join(os.path.dirname(save_path), "c2pa_temp_" + os.path.basename(save_path))
    os.rename(save_path, c2pa_temp)
    
    sign_result = sign_file(
        source_path=c2pa_temp,
        output_path=save_path,
        title=f"Project Iceberg Broadcast: {entry['original_name']}",
        watermark_payload_id=entry['payload_id'],
        distributed_to=entry.get('distributed_to')
    )
    
    if os.path.exists(c2pa_temp):
        os.remove(c2pa_temp)
        
    if sign_result.get("signed"):
        entry["c2pa_signature"] = "valid"
        entry["c2pa_manifest"] = sign_result.get("manifest_label")
    else:
        entry["c2pa_signature"] = "failed"
        
    entry["status"] = "ready"
    _broadcast_sync("upload", entry, loop)


@app.post("/api/register")
async def register_asset(background_tasks: BackgroundTasks, file: UploadFile = File(...), label: str = Form("official_broadcast"), distributed_to: str = Form(None)):
    ext = os.path.splitext(file.filename or "file")[1].lower()
    unique_name = f"{uuid.uuid4().hex[:8]}{ext}"
    temp_path = os.path.join(UPLOADS_DIR, f"temp_{unique_name}")
    save_path = os.path.join(MEDIA_DIR, unique_name)
    
    with open(temp_path, "wb") as out:
        shutil.copyfileobj(file.file, out)
        
    is_video = ext in [".mp4", ".mov", ".avi", ".mkv"]
    payload_tensor = watermark_engine.generate_random_payload()
    # convert binary payload to string representation for UI
    payload_str = "".join([str(int(x)) for x in payload_tensor[0].tolist()])[:8]
        
    entry = {
        "id": uuid.uuid4().hex[:8],
        "filename": unique_name,
        "original_name": file.filename,
        "label": label,
        "url": f"/media/{unique_name}",
        "c2pa_signature": "signing...", 
        "payload_id": payload_str,
        "distributed_to": distributed_to,
        "status": "processing",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    registered_files.append(entry)
    
    # Broadcast that it started processing
    await _broadcast_event("upload_start", entry)
    
    loop = asyncio.get_running_loop()
    background_tasks.add_task(process_upload_task, temp_path, save_path, is_video, entry, payload_tensor, loop)
    
    return entry

@app.get("/api/registered")
async def get_registered():
    return registered_files

@app.post("/api/verify")
async def verify_local_media(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "file")[1].lower()
    unique_name = f"verify_{uuid.uuid4().hex[:8]}{ext}"
    temp_path = os.path.join(UPLOADS_DIR, unique_name)
    
    with open(temp_path, "wb") as out:
        shutil.copyfileobj(file.file, out)
        
    try:
        # Check C2PA first
        val_result = validate_file(temp_path)
        
        # Then Algorithmic Block-Based DCT
        dct_payload = None
        is_video = ext in [".mp4", ".mov", ".avi", ".mkv"]
        
        try:
            # Algorithmic Block-Based DCT Payload Extraction using the trained model
            if is_video:
                import cv2
                import torchvision.transforms.functional as TF
                cap = cv2.VideoCapture(temp_path)
                ret, frame = cap.read()
                if ret:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    tensor = TF.to_tensor(rgb).unsqueeze(0).to(watermark_engine.device)
                    extracted = watermark_engine.extract_watermark(tensor)
                    dct_payload = "".join([str(int(x)) for x in extracted[0].round().tolist()])[:8]
                cap.release()
            else:
                from PIL import Image
                import torchvision.transforms.functional as TF
                img = Image.open(temp_path).convert("RGB")
                tensor = TF.to_tensor(img).unsqueeze(0).to(watermark_engine.device)
                extracted = watermark_engine.extract_watermark(tensor)
                dct_payload = "".join([str(int(x)) for x in extracted[0].round().tolist()])[:8]
        except Exception as e:
            print(f"[Verify] Watermark Extraction failed: {e}")
            
        return {
            "c2pa": val_result,
            "dct_payload": dct_payload
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/alerts")
async def get_alerts():
    return alerts_database

@app.post("/api/alerts")
async def post_alert(alert: dict):
    alert["id"] = uuid.uuid4().hex[:8]
    alert["timestamp"] = datetime.now(timezone.utc).isoformat()
    alerts_database.append(alert)
    await _broadcast_event("alert", alert)
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# API: Mock Clones (Simulation)
# ---------------------------------------------------------------------------

@app.post("/api/simulate-piracy")
async def simulate_piracy(request: Request):
    """
    Takes an official asset ID, strips its C2PA, adds noise (simulated),
    and publishes it to the mock YouTube or Twitch clone.
    """
    data = await request.json()
    asset_id = data.get("asset_id")
    platform = data.get("platform", "youtube")
    
    asset = next((a for a in registered_files if a["id"] == asset_id), None)
    if not asset:
        raise HTTPException(404, "Asset not found")
        
    # Create a "pirated" copy (we just use the same file but strip C2PA in metadata)
    # In a real scenario, this would apply FFmpeg compression
    post = {
        "post_id": uuid.uuid4().hex[:8],
        "title": f"MOCK PIRATED STREAM: {asset['original_name']} LIVE",
        "video_url": asset["url"],
        "c2pa_signature": "missing", # Stripped by the pirate
        "payload_id": asset["payload_id"],
        "views": random.randint(1000, 50000),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    clone_feeds[platform].insert(0, post)
    await _broadcast_event("piracy_simulated", post)
    return post

@app.get("/api/feed/{platform}")
async def get_feed(platform: str):
    if platform not in clone_feeds:
        return []
    return clone_feeds[platform]

# ---------------------------------------------------------------------------
# SSE
# ---------------------------------------------------------------------------

@app.get("/api/stream")
async def sse_stream():
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    sse_subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                msg = await queue.get()
                yield {"event": msg['type'], "data": json.dumps(msg['data'])}
        except asyncio.CancelledError:
            pass
        finally:
            if queue in sse_subscribers:
                sse_subscribers.remove(queue)

    return EventSourceResponse(event_generator())

# ---------------------------------------------------------------------------
# Frontend Catch-All
# ---------------------------------------------------------------------------

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve the React frontend for any unmatched route (Client-side routing)"""
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Frontend not built. Run 'npm run build' inside frontend/</h1>", 404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
