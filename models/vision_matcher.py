"""
Vision Matcher — ResNet50 Feature Extraction + FAISS Index
============================================================
Extracts deep feature embeddings from images/video frames using a
pretrained ResNet50 (on CUDA), and indexes them with FAISS for
fast nearest-neighbor similarity search.
"""

import torch
import torch.nn as nn
import torchvision.transforms as T
import torchvision.models as models
import numpy as np
import faiss
import cv2
import os
import json
import tempfile
import glob
from PIL import Image
import ffmpeg


class FeatureExtractor:
    """
    Wraps a pretrained ResNet50 with the classification head removed.
    Produces 2048-dimensional L2-normalized feature vectors.
    """

    def __init__(self, device=None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device

        # Load pretrained Swin Transformer V2 (Tiny)
        weights = models.Swin_V2_T_Weights.DEFAULT
        self.model = models.swin_v2_t(weights=weights)
        # Replace the classification head with Identity to extract 768-D embeddings
        self.model.head = nn.Identity()
        self.model = self.model.to(self.device)
        self.model.eval()

        self.transform = weights.transforms()
        self.dim = 768
        print(f"[Vision] Swin V2 feature extractor loaded on {self.device}")

    @torch.no_grad()
    def extract_from_pil(self, pil_image):
        """Extract a single feature vector from a PIL Image."""
        tensor = self.transform(pil_image.convert("RGB")).unsqueeze(0).to(self.device)
        feat = self.model(tensor).squeeze()
        feat = feat.cpu().numpy().astype(np.float32)
        if feat.ndim == 0:
            feat = feat.reshape(1)
        feat /= np.linalg.norm(feat) + 1e-8  # L2 normalize
        return feat

    @torch.no_grad()
    def extract_from_numpy(self, bgr_frame):
        """Extract a feature vector from a BGR numpy frame (OpenCV format)."""
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        return self.extract_from_pil(pil)

    @torch.no_grad()
    def extract_batch(self, pil_images):
        """Extract features from a list of PIL images. Returns (N, dim) array."""
        tensors = [self.transform(img.convert("RGB")) for img in pil_images]
        batch = torch.stack(tensors).to(self.device)
        feats = self.model(batch) # (N, dim)
        if feats.ndim == 1:
            feats = feats.unsqueeze(0)
        feats = feats.cpu().numpy().astype(np.float32)
        norms = np.linalg.norm(feats, axis=1, keepdims=True) + 1e-8
        feats /= norms
        return feats


class FingerprintIndex:
    """
    FAISS-backed index for storing and searching content fingerprints.
    Uses Inner Product (cosine similarity on L2-normalized vectors).
    """

    def __init__(self, dim=768, index_dir="data/faiss_index"):
        self.dim = dim
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)

        self.index_path = os.path.join(index_dir, "fingerprints.index")
        self.meta_path = os.path.join(index_dir, "metadata.json")

        # Load or create index
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            print(f"[FAISS] Loaded index with {self.index.ntotal} vectors")
        else:
            self.index = faiss.IndexFlatIP(dim)  # Inner product = cosine on normalized vecs
            print(f"[FAISS] Created new empty index (dim={dim})")

        # Load or create metadata
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = []  # list of {id, filename, source, timestamp, ...}

    @property
    def total(self):
        return self.index.ntotal

    def add_vectors(self, vectors, meta_entries):
        """
        Add vectors to the index.
        vectors: np.array (N, dim), L2-normalized
        meta_entries: list of dicts with at least {filename, source}
        """
        assert vectors.shape[1] == self.dim
        self.index.add(vectors)
        self.metadata.extend(meta_entries)
        self._save()
        print(f"[FAISS] Added {vectors.shape[0]} vectors. Total: {self.index.ntotal}")

    def search(self, query_vector, top_k=5):
        """
        Search for nearest neighbors.
        query_vector: np.array (dim,) — L2-normalized
        Returns: list of (similarity_score, metadata_dict)
        """
        if self.index.ntotal == 0:
            return []
        query = query_vector.reshape(1, -1).astype(np.float32)
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self.metadata[idx] if idx < len(self.metadata) else {}
            results.append((float(score), meta))
        return results

    def clear(self):
        """Reset the index."""
        self.index = faiss.IndexFlatIP(self.dim)
        self.metadata = []
        self._save()
        print("[FAISS] Index cleared")

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w") as f:
            json.dump(self.metadata, f)


class VisionMatcher:
    """
    High-level API combining FeatureExtractor + FingerprintIndex.
    Used by the engine to fingerprint uploads and match suspicious frames.
    """

    def __init__(self, index_dir="data/faiss_index", device=None):
        self.extractor = FeatureExtractor(device=device)
        self.index = FingerprintIndex(dim=self.extractor.dim, index_dir=index_dir)
        self.match_threshold = 0.65  # cosine similarity threshold

    def register_image(self, image_path, source="upload"):
        """Register a single image into the fingerprint database."""
        pil = Image.open(image_path).convert("RGB")
        feat = self.extractor.extract_from_pil(pil)
        meta = {
            "filename": os.path.basename(image_path),
            "source": source,
            "type": "image",
        }
        self.index.add_vectors(feat.reshape(1, -1), [meta])
        return meta

    def register_video(self, video_path, source="upload", max_frames=10):
        """
        Register a video by extracting frames at regular intervals
        using ffmpeg and indexing their feature embeddings.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pattern = os.path.join(tmpdir, "frame_%04d.jpg")
            try:
                # Extract frames using ffmpeg at 1 fps, up to max_frames
                (
                    ffmpeg
                    .input(video_path)
                    .filter('fps', fps=1)
                    .output(out_pattern, vframes=max_frames, format='image2', vcodec='mjpeg', q=2)
                    .run(quiet=True, capture_stdout=True, capture_stderr=True)
                )
            except ffmpeg.Error as e:
                print(f"[Vision] FFmpeg could not process video: {video_path}")
                return []

            frame_files = sorted(glob.glob(os.path.join(tmpdir, "*.jpg")))
            frames = []
            for img_path in frame_files:
                try:
                    frames.append(Image.open(img_path).copy())
                except:
                    pass

        if not frames:
            print(f"[Vision] No frames extracted from {video_path}")
            return []

        feats = self.extractor.extract_batch(frames)
        basename = os.path.basename(video_path)
        metas = [
            {
                "filename": basename,
                "source": source,
                "type": "video",
                "frame_index": i,
            }
            for i in range(len(frames))
        ]
        self.index.add_vectors(feats, metas)
        print(f"[Vision] Registered {len(frames)} frames from {basename}")
        return metas

    def match_frame(self, bgr_frame, top_k=3):
        """
        Match a single BGR frame against the fingerprint database.
        Returns list of (score, meta) above threshold.
        """
        feat = self.extractor.extract_from_numpy(bgr_frame)
        results = self.index.search(feat, top_k)
        matches = [(s, m) for s, m in results if s >= self.match_threshold]
        return matches

    def match_video_url(self, url, sample_frames=3, top_k=3):
        """
        Open a video URL (including .m3u8 HLS), extract sample frames
        safely with ffmpeg, and check each against the fingerprint database.
        Returns list of matches with frame details.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pattern = os.path.join(tmpdir, "frame_%04d.jpg")
            try:
                # Extract frames using ffmpeg at 1 fps, up to sample_frames
                (
                    ffmpeg
                    .input(url)
                    .filter('fps', fps=1)
                    .output(out_pattern, vframes=sample_frames, format='image2', vcodec='mjpeg', q=2)
                    .run(quiet=True, capture_stdout=True, capture_stderr=True)
                )
            except ffmpeg.Error as e:
                print(f"[Vision] FFmpeg could not open stream: {url}")
                return []

            frame_files = sorted(glob.glob(os.path.join(tmpdir, "*.jpg")))
            frames = []
            for img_path in frame_files:
                try:
                    frames.append(Image.open(img_path).copy())
                except:
                    pass

        all_matches = []
        for i, frame in enumerate(frames):
            # Convert PIL to BGR numpy array using cv2 to use existing match_frame which takes BGR numpy
            # Or just rewrite match_frame to take PIL? The method is match_frame(self, bgr_frame, top_k=3)
            # Let's convert PIL to BGR 
            import numpy as np
            bgr_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
            matches = self.match_frame(bgr_frame, top_k)
            if matches:
                best_score, best_meta = matches[0]
                all_matches.append({
                    "frame_position": i,
                    "similarity": best_score,
                    "matched_file": best_meta.get("filename", "unknown"),
                    "matched_source": best_meta.get("source", "unknown"),
                })

        return all_matches


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Vision Matcher — Standalone Test")
    print("=" * 60)

    matcher = VisionMatcher()
    print(f"\nIndex contains {matcher.index.total} fingerprints")

    # Create a dummy test image
    dummy = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    rgb = Image.fromarray(dummy)
    feat = matcher.extractor.extract_from_pil(rgb)
    print(f"Feature shape: {feat.shape}, norm: {np.linalg.norm(feat):.3f}")
    print("[Vision] Standalone test passed.")
