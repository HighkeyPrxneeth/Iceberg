"""Test C2PA signing - no TSA, no verify_after_sign."""
import os
import json
import c2pa
from PIL import Image
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_DIR = os.path.join(BASE_DIR, "keys")

test_jpg = os.path.join(BASE_DIR, "media", "test_input.jpg")
signed_jpg = os.path.join(BASE_DIR, "media", "test_signed.jpg")

img = Image.new("RGB", (200, 200), color=(0, 128, 255))
img.save(test_jpg, "JPEG")

with open(os.path.join(KEYS_DIR, "certificate.pem"), "r") as f:
    cert_pem = f.read()
with open(os.path.join(KEYS_DIR, "private_key.pem"), "rb") as f:
    key_data = f.read()

private_key = serialization.load_pem_private_key(key_data, password=None, backend=default_backend())

def signer_cb(data):
    return private_key.sign(data, ec.ECDSA(hashes.SHA256()))

manifest_def = {
    "claim_generator_info": [{"name": "test", "version": "0.1"}],
    "title": "Test",
    "assertions": [{"label": "c2pa.actions", "data": {"actions": [{"action": "c2pa.created"}]}}]
}

# Test 1: No TSA URL at all
print("--- Test 1: No TSA URL ---")
try:
    ctx = c2pa.Context.from_dict({
        "verify": {"verify_after_sign": False},
        "builder": {"thumbnail": {"enabled": False}},
    })
    signer = c2pa.Signer.from_callback(signer_cb, c2pa.C2paSigningAlg.ES256, cert_pem)
    with ctx:
        with signer:
            with c2pa.Builder(manifest_def, ctx) as builder:
                builder.sign_file(test_jpg, signed_jpg, signer)
    print(f"SUCCESS! ({os.path.getsize(signed_jpg)} bytes)")
except Exception as e:
    print(f"FAILED: {e}")

# Test 2: With TSA but also verify_after_sign=False  
print("\n--- Test 2: With TSA ---")
if os.path.exists(signed_jpg):
    os.remove(signed_jpg)
try:
    ctx = c2pa.Context.from_dict({
        "verify": {"verify_after_sign": False},
        "builder": {"thumbnail": {"enabled": False}},
    })
    signer = c2pa.Signer.from_callback(signer_cb, c2pa.C2paSigningAlg.ES256, cert_pem, "http://timestamp.digicert.com")
    with ctx:
        with signer:
            with c2pa.Builder(manifest_def, ctx) as builder:
                builder.sign_file(test_jpg, signed_jpg, signer)
    print(f"SUCCESS! ({os.path.getsize(signed_jpg)} bytes)")
except Exception as e:
    print(f"FAILED: {e}")

# Cleanup
for f in [test_jpg, signed_jpg]:
    if os.path.exists(f):
        os.remove(f)
