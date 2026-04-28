"""
Generate C2PA-compliant certificate chain for Project Iceberg.
Uses ES256 (ECDSA P-256) as required by the C2PA specification.

The C2PA SDK requires a proper certificate chain (not a bare self-signed cert).
This script generates:
  1. A Root CA self-signed certificate
  2. An end-entity signing certificate signed by the Root CA
  
The certificate PEM file contains the full chain (end-entity + root)
so the C2PA SDK can validate the chain internally.
"""

import os
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, ObjectIdentifier
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_DIR = os.path.join(BASE_DIR, "keys")

# C2PA-specific Extended Key Usage OID
C2PA_EKU_OID = ObjectIdentifier("1.3.6.1.4.1.53224.1.1")


def generate_keys():
    """Generate a Root CA + End-Entity certificate chain for C2PA."""
    os.makedirs(KEYS_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)

    # ─── Step 1: Root CA ────────────────────────────────────────
    root_key = ec.generate_private_key(ec.SECP256R1())
    root_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Project Iceberg Root CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Project Iceberg Root CA"),
    ])

    root_cert = (
        x509.CertificateBuilder()
        .subject_name(root_name)
        .issuer_name(root_name)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=False,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=True, crl_sign=True,
                encipher_only=False, decipher_only=False,
            ), critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(root_key.public_key()),
            critical=False,
        )
        .sign(root_key, hashes.SHA256())
    )

    print(f"[KeyGen] Root CA generated: {root_name}")

    # ─── Step 2: End-Entity Signing Certificate ─────────────────
    ee_key = ec.generate_private_key(ec.SECP256R1())
    ee_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Project Iceberg"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Project Iceberg C2PA Signer"),
    ])

    ee_cert = (
        x509.CertificateBuilder()
        .subject_name(ee_name)
        .issuer_name(root_name)  # Signed by Root CA
        .public_key(ee_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=True,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=False, crl_sign=False,
                encipher_only=False, decipher_only=False,
            ), critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.EMAIL_PROTECTION]),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ee_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(root_key.public_key()),
            critical=False,
        )
        .sign(root_key, hashes.SHA256())  # Signed by Root CA's key
    )

    print(f"[KeyGen] End-Entity cert generated: {ee_name}")

    # ─── Step 3: Save Files ─────────────────────────────────────
    # Private key (end-entity only — this is the signing key)
    key_path = os.path.join(KEYS_DIR, "private_key.pem")
    with open(key_path, "wb") as f:
        f.write(ee_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Certificate chain: end-entity + root CA (C2PA SDK needs the chain)
    cert_path = os.path.join(KEYS_DIR, "certificate.pem")
    with open(cert_path, "wb") as f:
        f.write(ee_cert.public_bytes(serialization.Encoding.PEM))
        f.write(root_cert.public_bytes(serialization.Encoding.PEM))

    # Also save Root CA separately (useful for trust anchor configuration)
    root_path = os.path.join(KEYS_DIR, "root_ca.pem")
    with open(root_path, "wb") as f:
        f.write(root_cert.public_bytes(serialization.Encoding.PEM))

    print(f"[KeyGen] Private key:   {key_path}")
    print(f"[KeyGen] Cert chain:    {cert_path} (end-entity + root)")
    print(f"[KeyGen] Root CA:       {root_path}")
    print(f"[KeyGen] Algorithm:     ECDSA P-256 (ES256)")
    print(f"[KeyGen] Valid until:   {(now + timedelta(days=365)).strftime('%Y-%m-%d')}")

    return key_path, cert_path


if __name__ == "__main__":
    print("=" * 60)
    print("  Project Iceberg - C2PA Key Generation")
    print("=" * 60)
    generate_keys()
    print("\nDone. Certificate chain is ready for C2PA signing.")
