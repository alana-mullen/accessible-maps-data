from pathlib import Path
import pytest

from accessible_maps.delta.models import DeltaManifest
from accessible_maps.delta.signing import (
    SigningError,
    generate_keypair,
    load_private_key,
    load_public_key,
    save_keypair,
    sign_bytes,
    sign_manifest,
    verify_manifest,
    verify_signature,
)


def test_keypair_generation():
    priv, pub = generate_keypair()
    assert isinstance(priv, str) and len(priv) > 0
    assert isinstance(pub, str) and len(pub) > 0

    priv_key = load_private_key(priv)
    pub_key = load_public_key(pub)
    assert priv_key is not None
    assert pub_key is not None


def test_sign_and_verify_bytes():
    priv_b64, pub_b64 = generate_keypair()
    payload = b"accessibility-dataset-payload-bytes"

    sig = sign_bytes(payload, priv_b64)
    assert verify_signature(payload, sig, pub_b64)

    # Tampered payload fails
    assert not verify_signature(b"tampered-payload", sig, pub_b64)

    # Invalid public key fails
    _, other_pub = generate_keypair()
    assert not verify_signature(payload, sig, other_pub)


def test_save_and_load_keypair(tmp_path: Path):
    priv_path, pub_path = save_keypair(tmp_path, prefix="test_key")
    assert priv_path.is_file()
    assert pub_path.is_file()

    priv_key = load_private_key(priv_path)
    pub_key = load_public_key(pub_path)

    payload = b"test with pem files"
    sig = sign_bytes(payload, priv_key)
    assert verify_signature(payload, sig, pub_key)


def test_sign_and_verify_manifest():
    priv_b64, pub_b64 = generate_keypair()
    manifest = DeltaManifest(
        dataset_name="north-west",
        base_version="2026.01",
        target_version="2026.02",
        base_sha256="abc",
        target_sha256="def",
    )

    sign_manifest(manifest, priv_b64)
    assert manifest.signature is not None
    assert manifest.public_key == pub_b64

    # Verify with embedded public key
    assert verify_manifest(manifest)

    # Verify with explicit public key
    assert verify_manifest(manifest, pub_b64)

    # Tampering with manifest content invalidates signature
    manifest.target_version = "2026.03"
    assert not verify_manifest(manifest)


def test_invalid_key_raises():
    with pytest.raises(SigningError):
        load_private_key("invalid-key-data")

    with pytest.raises(SigningError):
        load_public_key("invalid-key-data")
