from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)

if TYPE_CHECKING:
    from .models import DeltaManifest


class SigningError(RuntimeError):
    """Raised when cryptographic signing or verification fails."""


def generate_keypair() -> tuple[str, str]:
    """Generate a new Ed25519 keypair, returned as raw 32-byte Base64 strings (private, public)."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_raw = private_key.private_bytes_raw()
    pub_raw = public_key.public_bytes_raw()

    return (
        base64.b64encode(priv_raw).decode("ascii"),
        base64.b64encode(pub_raw).decode("ascii"),
    )


def save_keypair(
    directory: Path,
    prefix: str = "delta_key",
) -> tuple[Path, Path]:
    """Generate and save PEM-formatted Ed25519 keypair to a directory."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )
    pub_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path = directory / f"{prefix}.pem"
    pub_path = directory / f"{prefix}.pub"

    priv_path.write_bytes(priv_pem)
    pub_path.write_bytes(pub_pem)

    return priv_path, pub_path


def load_private_key(key_input: str | Path | Ed25519PrivateKey) -> Ed25519PrivateKey:
    """Load an Ed25519 private key from instance, PEM/raw Base64 string, or file path."""
    if isinstance(key_input, Ed25519PrivateKey):
        return key_input

    if isinstance(key_input, Path) or (isinstance(key_input, str) and Path(key_input).is_file()):
        try:
            data = Path(key_input).read_bytes()
            if b"BEGIN PRIVATE KEY" in data:
                return load_pem_private_key(data, password=None)  # type: ignore
            try:
                raw_bytes = base64.b64decode(data.strip())
                if len(raw_bytes) == 32:
                    return Ed25519PrivateKey.from_private_bytes(raw_bytes)
            except Exception:
                pass
            if len(data) == 32:
                return Ed25519PrivateKey.from_private_bytes(data)
        except Exception as exc:
            raise SigningError(f"Failed to read private key from file: {exc}") from exc

    if isinstance(key_input, str):
        key_str = key_input.strip()
        if "BEGIN PRIVATE KEY" in key_str:
            try:
                return load_pem_private_key(key_str.encode("utf-8"), password=None)  # type: ignore
            except Exception as exc:
                raise SigningError(f"Invalid PEM private key: {exc}") from exc
        try:
            raw_bytes = base64.b64decode(key_str)
            if len(raw_bytes) == 32:
                return Ed25519PrivateKey.from_private_bytes(raw_bytes)
        except Exception:
            pass

    raise SigningError("Invalid or unsupported Ed25519 private key format")


def load_public_key(key_input: str | Path | Ed25519PublicKey) -> Ed25519PublicKey:
    """Load an Ed25519 public key from instance, PEM/raw Base64 string, or file path."""
    if isinstance(key_input, Ed25519PublicKey):
        return key_input

    if isinstance(key_input, Path) or (isinstance(key_input, str) and Path(key_input).is_file()):
        try:
            data = Path(key_input).read_bytes()
            if b"BEGIN PUBLIC KEY" in data:
                return load_pem_public_key(data)  # type: ignore
            try:
                raw_bytes = base64.b64decode(data.strip())
                if len(raw_bytes) == 32:
                    return Ed25519PublicKey.from_public_bytes(raw_bytes)
            except Exception:
                pass
            if len(data) == 32:
                return Ed25519PublicKey.from_public_bytes(data)
        except Exception as exc:
            raise SigningError(f"Failed to read public key from file: {exc}") from exc

    if isinstance(key_input, str):
        key_str = key_input.strip()
        if "BEGIN PUBLIC KEY" in key_str:
            try:
                return load_pem_public_key(key_str.encode("utf-8"))  # type: ignore
            except Exception as exc:
                raise SigningError(f"Invalid PEM public key: {exc}") from exc
        try:
            raw_bytes = base64.b64decode(key_str)
            if len(raw_bytes) == 32:
                return Ed25519PublicKey.from_public_bytes(raw_bytes)
        except Exception:
            pass

    raise SigningError("Invalid or unsupported Ed25519 public key format")


def sign_bytes(data: bytes, private_key_input: str | Path | Ed25519PrivateKey) -> str:
    """Sign bytes payload using Ed25519 private key, returning Base64 signature."""
    private_key = load_private_key(private_key_input)
    signature = private_key.sign(data)
    return base64.b64encode(signature).decode("ascii")


def verify_signature(
    data: bytes,
    signature_b64: str,
    public_key_input: str | Path | Ed25519PublicKey,
) -> bool:
    """Verify Base64 Ed25519 signature over bytes payload."""
    try:
        public_key = load_public_key(public_key_input)
        signature = base64.b64decode(signature_b64)
        public_key.verify(signature, data)
        return True
    except (InvalidSignature, ValueError, SigningError):
        return False


def sign_manifest(
    manifest: DeltaManifest,
    private_key_input: str | Path | Ed25519PrivateKey,
) -> DeltaManifest:
    """Sign manifest canonical bytes and attach signature and public key."""
    private_key = load_private_key(private_key_input)
    pub_raw = private_key.public_key().public_bytes_raw()
    pub_b64 = base64.b64encode(pub_raw).decode("ascii")

    manifest.public_key = pub_b64
    manifest.signature = None  # Clear previous signature before computing canonical payload
    canonical_data = manifest.canonical_bytes()
    manifest.signature = sign_bytes(canonical_data, private_key)
    return manifest


def verify_manifest(
    manifest: DeltaManifest,
    public_key_input: str | Path | Ed25519PublicKey | None = None,
) -> bool:
    """Verify manifest signature against the given public key or the one stored in manifest."""
    if not manifest.signature:
        return False

    key_to_use = public_key_input or manifest.public_key
    if not key_to_use:
        return False

    canonical_data = manifest.canonical_bytes()
    return verify_signature(canonical_data, manifest.signature, key_to_use)
