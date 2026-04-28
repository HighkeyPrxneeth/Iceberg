"""
Generate Mock Media
====================
Uses ffmpeg to create dummy video content and HLS streams
for the PoC mock environment.

Creates:
  media/official_highlight.mp4    — The "official" reference content
  media/suspicious_stream/        — HLS stream (.m3u8 + .ts segments)
"""

import subprocess
import os
import sys


MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
OFFICIAL_MP4 = os.path.join(MEDIA_DIR, "official_highlight.mp4")
SUSPICIOUS_DIR = os.path.join(MEDIA_DIR, "suspicious_stream")
SUSPICIOUS_M3U8 = os.path.join(SUSPICIOUS_DIR, "stream.m3u8")


def check_ffmpeg():
    """Verify ffmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            print(f"[Media] Found: {version_line}")
            return True
    except FileNotFoundError:
        pass
    print("[Media] ERROR: ffmpeg not found in PATH")
    return False


def generate_official_video():
    """
    Generate a synthetic 'official sports broadcast' video.
    Uses ffmpeg test sources to create distinctive visual content
    with overlaid text simulating broadcast graphics.
    """
    os.makedirs(MEDIA_DIR, exist_ok=True)

    if os.path.exists(OFFICIAL_MP4):
        print(f"[Media] Official video already exists: {OFFICIAL_MP4}")
        return OFFICIAL_MP4

    print("[Media] Generating official highlight video...")

    # Create a 15-second synthetic broadcast with:
    # - SMPTE test pattern background (distinctive, fingerprintable)
    # - Overlaid text simulating a sports broadcast lower-third
    # - Synthetic sine wave audio
    cmd = [
        "ffmpeg", "-y",
        # Video: SMPTE color bars (distinctive, fingerprintable)
        "-f", "lavfi",
        "-i", "smptebars=size=640x360:rate=30:duration=15",
        # Audio: sine wave tone
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=15",
        # Encoding
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        OFFICIAL_MP4,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"[Media] ffmpeg error:\n{result.stderr[-500:]}")
        sys.exit(1)

    size = os.path.getsize(OFFICIAL_MP4)
    print(f"[Media] Created official video: {OFFICIAL_MP4} ({size:,} bytes)")
    return OFFICIAL_MP4


def generate_suspicious_stream():
    """
    Generate a 'pirated' HLS stream from the official video.
    Simulates common piracy transformations:
    - Slight color shift
    - Horizontal flip
    - Lower quality re-encoding
    - Added border/watermark
    """
    os.makedirs(SUSPICIOUS_DIR, exist_ok=True)

    if os.path.exists(SUSPICIOUS_M3U8):
        print(f"[Media] Suspicious stream already exists: {SUSPICIOUS_M3U8}")
        return SUSPICIOUS_M3U8

    if not os.path.exists(OFFICIAL_MP4):
        print("[Media] Official video not found, generating first...")
        generate_official_video()

    print("[Media] Generating suspicious HLS stream (pirated copy)...")

    # Apply piracy-style transformations:
    # 1. Horizontal flip (common piracy evasion)
    # 2. Slight color shift (hue rotation)
    # 3. Add a fake watermark
    # 4. Re-encode at lower quality
    # 5. Output as HLS segments
    cmd = [
        "ffmpeg", "-y",
        "-i", OFFICIAL_MP4,
        # Piracy transformations: flip, hue shift, black border padding
        "-vf", (
            "hflip,"
            "hue=h=15,"
            "pad=w=iw+20:h=ih+20:x=10:y=10:color=black"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-c:a", "aac", "-b:a", "96k",
        "-pix_fmt", "yuv420p",
        # HLS output options
        "-hls_time", "2",
        "-hls_list_size", "0",
        "-hls_segment_filename", os.path.join(SUSPICIOUS_DIR, "segment_%03d.ts"),
        SUSPICIOUS_M3U8,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"[Media] ffmpeg error:\n{result.stderr[-500:]}")
        sys.exit(1)

    # Count segments
    segments = [f for f in os.listdir(SUSPICIOUS_DIR) if f.endswith(".ts")]
    print(f"[Media] Created HLS stream: {SUSPICIOUS_M3U8}")
    print(f"[Media]   Segments: {len(segments)} .ts files")
    return SUSPICIOUS_M3U8


def generate_all():
    """Generate all mock media files."""
    if not check_ffmpeg():
        print("[Media] Cannot proceed without ffmpeg.")
        sys.exit(1)

    print()
    official = generate_official_video()
    print()
    stream = generate_suspicious_stream()
    print()
    print("[Media] All mock media generated successfully!")
    print(f"  Official:   {official}")
    print(f"  Suspicious: {stream}")
    return official, stream


if __name__ == "__main__":
    generate_all()
