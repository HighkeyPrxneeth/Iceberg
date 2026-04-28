"""
C2PA Content Provenance Utilities
==================================
Provides real C2PA manifest signing and validation using the official
c2pa-python SDK (Python binding for c2pa-rs).

This module:
  1. Signs media files with a tamper-evident C2PA manifest containing
     assertions about origin, authorship, and processing actions.
  2. Validates incoming media by reading the C2PA manifest store and
     checking the cryptographic signature + content hash integrity.

The CNN watermark engine runs BEFORE this module. The pipeline is:
  raw upload -> CNN watermark embedding -> C2PA signing -> output file
"""

import json
import os
from typing import Optional

import c2pa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_DIR = os.path.join(BASE_DIR, "keys")
CERT_PATH = os.path.join(KEYS_DIR, "certificate.pem")
KEY_PATH = os.path.join(KEYS_DIR, "private_key.pem")
ROOT_CA_PATH = os.path.join(KEYS_DIR, "root_ca.pem")

# Mapping from file extensions to MIME types for C2PA
MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
}


def _get_mime(filepath: str) -> str:
    """Determine the MIME type from a file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    mime = MIME_MAP.get(ext)
    if not mime:
        raise ValueError(f"Unsupported file format for C2PA: {ext}")
    return mime


def _load_credentials():
    """Load the private key and certificate chain from disk."""
    if not os.path.exists(CERT_PATH):
        raise FileNotFoundError(f"Certificate not found: {CERT_PATH}")
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(f"Private key not found: {KEY_PATH}")

    with open(CERT_PATH, "r") as f:
        cert_pem = f.read()  # PEM chain as string (end-entity + root CA)
    with open(KEY_PATH, "rb") as f:
        key_data = f.read()  # PEM bytes for the private key

    return cert_pem, key_data


def _make_callback_signer(key_data: bytes):
    """
    Create an ES256 callback signer function.
    
    The C2PA SDK calls this function with the data to sign,
    and we use the private key to produce the ECDSA signature.
    """
    private_key = serialization.load_pem_private_key(
        key_data,
        password=None,
        backend=default_backend(),
    )

    def signer_callback(data: bytes) -> bytes:
        """ECDSA-SHA256 signing callback."""
        return private_key.sign(data, ec.ECDSA(hashes.SHA256()))

    return signer_callback


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------

def build_manifest_definition(
    title: str = "Official Sports Broadcast",
    claim_generator: str = "ProjectIceberg/1.0",
    author: str = "Project Iceberg Platform",
    description: str = "Authenticated and watermarked by Project Iceberg.",
    watermark_payload_id: Optional[str] = None,
    distributed_to: Optional[str] = None,
) -> dict:
    """
    Build a C2PA manifest definition as a dictionary.
    
    This defines the assertions that will be cryptographically bound
    to the media file. Includes:
      - c2pa.actions: what processing was done (created, watermarked)
      - stds.schema-org.CreativeWork: authorship metadata
      - Optionally: custom assertion for watermark payload ID
    """
    actions = [
        {
            "action": "c2pa.created",
            "softwareAgent": claim_generator,
            "digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/digitalCreation",
        },
        {
            "action": "c2pa.edited",
            "softwareAgent": claim_generator,
            "parameters": {
                "description": "CNN steganographic watermark embedded."
            },
        },
    ]

    assertions = [
        {
            "label": "c2pa.actions",
            "data": {"actions": actions}
        },
        {
            "label": "stds.schema-org.CreativeWork",
            "data": {
                "@context": "https://schema.org",
                "@type": "VideoObject",
                "author": [
                    {
                        "@type": "Organization",
                        "name": author,
                    }
                ],
                "description": description,
            }
        },
    ]

    # Embed watermark payload ID as a custom assertion
    if watermark_payload_id:
        assertions.append({
            "label": "com.projecticeberg.watermark",
            "data": {
                "payload_id": watermark_payload_id,
                "method": "2D-CNN-Steganography",
                "payload_size_bits": 32,
            }
        })

    if distributed_to:
        assertions.append({
            "label": "com.projecticeberg.distribution",
            "data": {
                "distributed_to": distributed_to
            }
        })

    manifest = {
        "claim_generator_info": [
            {"name": "ProjectIceberg", "version": "1.0"}
        ],
        "title": title,
        "assertions": assertions,
    }

    return manifest


def sign_file(
    source_path: str,
    output_path: str,
    title: str = "Official Sports Broadcast",
    watermark_payload_id: Optional[str] = None,
    distributed_to: Optional[str] = None,
) -> dict:
    """
    Sign a media file with a C2PA manifest.
    
    This:
      1. Loads the private key and X.509 certificate chain
      2. Builds a manifest definition with assertions
      3. Uses the C2PA SDK to hash the file, build JUMBF, sign it,
         and inject the signed manifest into the output file
    
    Args:
        source_path: Path to the watermarked media file (input)
        output_path: Path for the C2PA-signed output file
        title: Human-readable title for the manifest
        watermark_payload_id: CNN watermark payload ID string
    
    Returns:
        dict with signing results: {signed: bool, manifest_label, ...}
    """
    cert_pem, key_data = _load_credentials()
    mime_type = _get_mime(source_path)

    manifest_def = build_manifest_definition(
        title=title,
        watermark_payload_id=watermark_payload_id,
        distributed_to=distributed_to,
    )

    signer_callback = _make_callback_signer(key_data)

    try:
        # Load Root CA for trust configuration
        root_ca_pem = ""
        if os.path.exists(ROOT_CA_PATH):
            with open(ROOT_CA_PATH, "r") as f:
                root_ca_pem = f.read()

        # Configure context: trust our Root CA, disable post-sign verification
        # (we validate separately via validate_file with proper trust config)
        ctx_config = {
            "verify": {"verify_after_sign": False},
            "builder": {
                "thumbnail": {"enabled": False},
            },
        }

        with c2pa.Context.from_dict(ctx_config) as ctx:
            with c2pa.Signer.from_callback(
                signer_callback,
                c2pa.C2paSigningAlg.ES256,
                cert_pem,
                "http://timestamp.digicert.com",
            ) as signer:
                with c2pa.Builder(manifest_def, ctx) as builder:
                    builder.sign_file(source_path, output_path, signer)

        print(f"[C2PA] [OK] Signed: {os.path.basename(output_path)}")

        result = {
            "signed": True,
            "source": os.path.basename(source_path),
            "output": os.path.basename(output_path),
            "mime_type": mime_type,
        }

        # Validate what we just signed
        validation = validate_file(output_path)
        result["manifest_label"] = validation.get("active_manifest", "unknown")
        result["validation_status"] = validation.get("status", "unknown")

        return result

    except Exception as e:
        print(f"[C2PA] [FAIL] Signing failed: {e}")
        return {
            "signed": False,
            "error": str(e),
            "source": os.path.basename(source_path),
        }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_file(filepath: str) -> dict:
    """
    Validate a media file's C2PA manifest.
    
    This:
      1. Parses the JUMBF manifest from the file container
      2. Verifies the cryptographic signature using the embedded certificate
      3. Recalculates the content hash and compares it to the manifest's data hash
    
    Args:
        filepath: Path to the media file to validate
    
    Returns:
        dict with validation results:
          - status: "valid" | "invalid" | "no_manifest"
          - active_manifest: manifest label if present
          - assertions: list of assertion labels
          - validation_errors: any errors found
    """
    try:
        # Load Root CA to trust our self-signed chain
        ctx_config = {}
        if os.path.exists(ROOT_CA_PATH):
            with open(ROOT_CA_PATH, "r") as f:
                root_ca_pem = f.read()
            ctx_config["trust"] = {"user_anchors": root_ca_pem}

        with c2pa.Context.from_dict(ctx_config) as ctx:
            with c2pa.Reader(filepath, context=ctx) as reader:
                raw_json = reader.json()
                manifest_store = json.loads(raw_json)

        active_label = manifest_store.get("active_manifest", "")
        manifests = manifest_store.get("manifests", {})
        active = manifests.get(active_label, {})

        # Check for validation_status (errors)
        validation_status = manifest_store.get("validation_status", [])

        assertions = []
        for a in active.get("assertions", []):
            assertions.append(a.get("label", "unknown"))

        # Extract our custom watermark assertion if present
        watermark_info = None
        distributed_to = None
        for a in active.get("assertions", []):
            if a.get("label") == "com.projecticeberg.watermark":
                watermark_info = a.get("data", {})
            elif a.get("label") == "com.projecticeberg.distribution":
                distributed_to = a.get("data", {}).get("distributed_to")

        result = {
            "status": "valid" if not validation_status else "invalid",
            "active_manifest": active_label,
            "claim_generator": active.get("claim_generator", ""),
            "title": active.get("title", ""),
            "assertions": assertions,
            "watermark_info": watermark_info,
            "distributed_to": distributed_to,
            "validation_errors": validation_status,
            "signature_info": active.get("signature_info", {}),
        }

        if validation_status:
            print(f"[C2PA] [!!] Validation issues: {validation_status}")
        else:
            print(f"[C2PA] [OK] Valid manifest: {active_label}")

        return result

    except Exception as e:
        error_msg = str(e)
        if "no manifest" in error_msg.lower() or "jumbf" in error_msg.lower() or "manifestnotfound" in error_msg.lower():
            print(f"[C2PA] [--] No C2PA manifest in: {os.path.basename(filepath)}")
            return {"status": "no_manifest", "error": error_msg}
        else:
            print(f"[C2PA] [FAIL] Validation error: {e}")
            return {"status": "error", "error": error_msg}


def validate_file_quick(filepath: str) -> str:
    """
    Quick validation returning just the status string.
    Returns: "valid", "invalid", "no_manifest", or "error"
    """
    result = validate_file(filepath)
    return result.get("status", "error")


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  C2PA Utilities -- Standalone Test")
    print("=" * 60)

    # Check if test media exists
    test_media = os.path.join(BASE_DIR, "media", "official_highlight.mp4")
    if not os.path.exists(test_media):
        print(f"[Test] No test media found at {test_media}")
        print("[Test] Run generate_mock_media.py first.")
        exit(1)

    # Test signing
    signed_output = os.path.join(BASE_DIR, "media", "test_signed.mp4")
    print("\n--- Signing ---")
    result = sign_file(
        test_media,
        signed_output,
        title="Test Signed Broadcast",
        watermark_payload_id="10110011",
    )
    print(json.dumps(result, indent=2))

    # Test validation on signed file
    if result.get("signed"):
        print("\n--- Validating Signed File ---")
        val_result = validate_file(signed_output)
        print(json.dumps(val_result, indent=2))

    # Test validation on unsigned file
    print("\n--- Validating Unsigned File ---")
    val_result2 = validate_file(test_media)
    print(json.dumps(val_result2, indent=2))

    # Cleanup
    if os.path.exists(signed_output):
        os.remove(signed_output)
        print(f"\n[Test] Cleaned up {signed_output}")
