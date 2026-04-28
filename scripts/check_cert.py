"""Check existing certificate details."""
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives.asymmetric import ec, rsa

cert = load_pem_x509_certificate(open("keys/certificate.pem", "rb").read())
print("Subject:", cert.subject)
print("Issuer:", cert.issuer)
print("Not valid after:", cert.not_valid_after_utc)
key = cert.public_key()
if isinstance(key, ec.EllipticCurvePublicKey):
    print(f"Key type: EC ({key.curve.name})")
elif isinstance(key, rsa.RSAPublicKey):
    print(f"Key type: RSA ({key.key_size} bits)")
else:
    print(f"Key type: {type(key)}")
print("Signature algo:", cert.signature_algorithm_oid._name)

# Check C2PA EKU
for ext in cert.extensions:
    print(f"Extension: {ext.oid._name} = {ext.value}")
