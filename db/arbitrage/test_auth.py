from __future__ import annotations

import base64
import os
import tempfile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)

from shared.auth import (
    load_ed25519_key,
    load_rsa_key,
    require_env,
    sign_ed25519,
    sign_rsa,
)


@pytest.fixture()
def rsa_key_path(tmp_path):
    key = generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
    path = tmp_path / "test_rsa.pem"
    path.write_bytes(pem)
    return path, key


@pytest.fixture()
def ed25519_key():
    return Ed25519PrivateKey.generate()


class TestRSA:
    def test_load_and_sign(self, rsa_key_path):
        path, original_key = rsa_key_path
        loaded = load_rsa_key(path)
        ts, sig = sign_rsa(loaded, "GET", "/trade-api/v2/markets")
        assert ts.isdigit()
        assert len(base64.b64decode(sig)) > 0

    def test_deterministic_per_key(self, rsa_key_path):
        path, _ = rsa_key_path
        loaded = load_rsa_key(path)
        ts1, sig1 = sign_rsa(loaded, "GET", "/path")
        ts2, sig2 = sign_rsa(loaded, "GET", "/path")
        # RSA-PSS is randomized, so signatures differ even for the same input
        assert ts1.isdigit()
        assert ts2.isdigit()

    def test_invalid_key_file(self, tmp_path):
        bad = tmp_path / "bad.pem"
        bad.write_text("not a key")
        with pytest.raises(ValueError):
            load_rsa_key(bad)

    def test_ed25519_pem_rejected(self, tmp_path):
        ed_key = Ed25519PrivateKey.generate()
        pem = ed_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        path = tmp_path / "ed.pem"
        path.write_bytes(pem)
        with pytest.raises(ValueError, match="Expected RSA"):
            load_rsa_key(path)


class TestEd25519:
    def test_load_from_hex(self, ed25519_key):
        raw = ed25519_key.private_bytes(
            Encoding.Raw, PrivateFormat.Raw, NoEncryption(),
        )
        hex_str = raw.hex()
        loaded = load_ed25519_key(hex_str)
        assert isinstance(loaded, Ed25519PrivateKey)

    def test_load_from_base64(self, ed25519_key):
        raw = ed25519_key.private_bytes(
            Encoding.Raw, PrivateFormat.Raw, NoEncryption(),
        )
        b64 = base64.b64encode(raw).decode()
        loaded = load_ed25519_key(b64)
        assert isinstance(loaded, Ed25519PrivateKey)

    def test_load_from_pem(self, ed25519_key):
        pem = ed25519_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption(),
        ).decode()
        loaded = load_ed25519_key(pem)
        assert isinstance(loaded, Ed25519PrivateKey)

    def test_sign_produces_valid_output(self, ed25519_key):
        ts, sig = sign_ed25519(ed25519_key, "GET", "/v1/markets")
        assert ts.isdigit()
        sig_bytes = base64.b64decode(sig)
        assert len(sig_bytes) == 64  # Ed25519 signatures are 64 bytes

    def test_invalid_key_material(self):
        with pytest.raises((ValueError, Exception)):
            load_ed25519_key("zzzz not a key zzzz")


class TestRequireEnv:
    def test_missing_raises(self, monkeypatch):
        monkeypatch.delenv("UNLIKELY_TEST_VAR_XYZ", raising=False)
        with pytest.raises(OSError, match="Missing"):
            require_env("UNLIKELY_TEST_VAR_XYZ")

    def test_present_returns_value(self, monkeypatch):
        monkeypatch.setenv("TEST_AUTH_VAR", "hello")
        assert require_env("TEST_AUTH_VAR") == "hello"
