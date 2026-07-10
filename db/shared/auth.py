from __future__ import annotations

import base64
import os
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import (
    load_der_private_key,
    load_pem_private_key,
)


def load_rsa_key(path: Path) -> RSAPrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, RSAPrivateKey):
        raise ValueError(f"Expected RSA private key, got {type(key).__name__}")
    return key


def sign_rsa(key: RSAPrivateKey, method: str, path: str) -> tuple[str, str]:
    timestamp = str(int(time.time() * 1000))
    message = (timestamp + method + path).encode()
    sig = key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return timestamp, base64.b64encode(sig).decode()


def load_ed25519_key(key_material: str) -> Ed25519PrivateKey:
    cleaned = key_material.strip()
    if cleaned.startswith("-----"):
        key = load_pem_private_key(cleaned.encode(), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError(f"Expected Ed25519 key, got {type(key).__name__}")
        return key
    cleaned = cleaned.replace("\n", "").replace("\r", "").replace(" ", "")
    try:
        raw = bytes.fromhex(cleaned)
    except ValueError:
        raw = base64.b64decode(cleaned)
    if len(raw) == 32:
        return Ed25519PrivateKey.from_private_bytes(raw)
    if len(raw) == 64:
        return Ed25519PrivateKey.from_private_bytes(raw[:32])
    key = load_der_private_key(raw, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError(f"Expected Ed25519 key, got {type(key).__name__}")
    return key


def sign_ed25519(key: Ed25519PrivateKey, method: str, path: str) -> tuple[str, str]:
    timestamp = str(int(time.time() * 1000))
    message = (timestamp + method + path).encode()
    sig = key.sign(message)
    return timestamp, base64.b64encode(sig).decode()


def require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise OSError(f"Missing required environment variable: {name}")
    return val
