# Project Iceberg v3.1 — Dual-Level Verification Engine Specification

Here is the technical specification for Project Iceberg v3.1, a proof-of-concept platform designed to authenticate media (such as sports broadcasts) and track its unauthorized propagation in real time. It is built to reliably detect piracy by implementing a dual-level verification system encompassing cryptographic metadata and robust steganography, accounting for adversarial modifications like compression and metadata stripping.

### **Level 1 Verification: C2PA Metadata Authentication (The First Pass)**
Before running heavy pixel-level analysis, the system checks for cryptographic proof of ownership. 

* **How it works:** The system extracts file metadata or stream manifests and validates C2PA signatures. 
* **The Benefit:** If a stream contains a valid, unbroken signature from the official broadcast infrastructure, the system immediately recognizes it as authorized, saving compute power. If the signature is deliberately stripped or broken by pirates, it proceeds to Level 2 verification.

### **Level 2 Verification: Algorithmic DCT Watermarking (Deep Structural Analysis)**
When C2PA is stripped, the system falls back to an invisible, compression-proof payload embedded directly into the media's frequency domain.

* **How it works:** Using an Algorithmic Block-Based DCT (Discrete Cosine Transform) approach, a 32-bit payload is invisibly embedded into the mid-frequency DCT coefficients (e.g., comparing coordinates (5, 5) vs (4, 4) in 8x8 blocks). 
* **The Benefit:** This technique solves the overfitting and perceptual artifact issues of traditional CNN autoencoders. Because the watermark alters structural frequencies that heavily compressed pipelines preserve, the payload survives massive degradation, screen recording, and JPEG/MP4 compression schemas, guaranteeing robust IP tracking.

---

### System Architecture & Components

The system architecture operates as a distributed environment, supporting horizontal scaling through asynchronous services and multiprocessing queues.

* **Component 1 (API Server):** A FastAPI backend managing reference media uploads, C2PA signature injection/validation, Mock API clone feeds (simulating YouTube/Twitch), and SSE (Server-Sent Events) for real-time dashboard updates.
* **Component 2 (Frontend Interface):** A modern React single-page application built with Vite, displaying a live verification log, asset management dashboard, and piracy simulation controls.
* **Component 3 (Message Queues):** Python multiprocessing.Queue buffers traffic streams locally between worker instances (acting as a lightweight message broker).
* **Component 4 (Crawler Worker):** A daemon process that continuously polls the mock social feeds. It checks for C2PA credentials and pushes suspicious, unauthenticated/stripped URLs to the anomaly queue.
* **Component 5 (Verifier Worker):** A standalone worker that pulls suspicious URLs from the queue. It uses OpenCV and PyTorch to ingest frames and extracts the DCT watermark payload. If the 32-bit payload matches a registered asset, it fires an alert webhook back to the FastAPI server to declare piracy.

### Technology Stack
* **Web Backend:** FastAPI, Uvicorn, Python, SSE-Starlette
* **Web Frontend:** React, Vite, HTML/CSS (Client-side routing)
* **Messaging / Concurrency:** Python multiprocessing
* **Computer Vision & Media:** OpenCV (cv2), PIL, PyTorch (for tensor ops/device management)
* **Cryptographic Metadata:** C2PA standard utilities
* **Watermarking Algorithm:** Block-Based Discrete Cosine Transform (DCT)
