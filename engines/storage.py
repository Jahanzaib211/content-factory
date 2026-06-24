"""
Storage backends (engines/storage.py).

Picks one of:
  - LocalStorageEngine  — writes to a local directory (default, no setup)
  - SeaweedFSEngine     — S3-compatible self-hosted object store (Apache-2.0, 33k★)
  - S3StorageEngine     — legacy AWS S3 path (uses the existing s3_uploader.py)

The STORAGE_BACKEND env var selects the backend. Default: "local".
Existing s3_uploader.py is preserved as the AWS path and is wrapped
behind the S3StorageEngine — no code change to the existing uploader.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, BinaryIO, Optional

from .base import BaseEngine, EngineCapability, EngineHealth, EngineResult, engine_method, EngineError

log = logging.getLogger(__name__)

STORAGE_BACKEND_ENV = "STORAGE_BACKEND"  # "local" | "seaweedfs" | "s3"
LOCAL_STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join("output", "storage"))


class LocalStorageEngine(BaseEngine):
    provider_id = "local"
    display_name = "Local filesystem (default)"
    capability = EngineCapability.STORAGE
    cost_hint = "Free (uses your disk)"
    hardware_hint = "any"
    requires_key = False
    key_env_var = None

    def __init__(self) -> None:
        os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

    async def health(self) -> EngineHealth:
        try:
            test = os.path.join(LOCAL_STORAGE_DIR, ".health")
            with open(test, "w") as f:
                f.write("ok")
            os.remove(test)
            return EngineHealth(healthy=True, detail=f"dir={LOCAL_STORAGE_DIR}")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        path = os.path.join(LOCAL_STORAGE_DIR, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return {"key": key, "size": len(data), "path": path, "url": f"/storage/{key}"}

    @engine_method
    def get(self, key: str) -> bytes:
        path = os.path.join(LOCAL_STORAGE_DIR, key)
        if not os.path.exists(path):
            raise EngineError(f"key not found: {key}")
        with open(path, "rb") as f:
            return f.read()

    @engine_method
    def delete(self, key: str) -> Dict[str, Any]:
        path = os.path.join(LOCAL_STORAGE_DIR, key)
        if os.path.exists(path):
            os.remove(path)
        return {"deleted": key}

    @engine_method
    def url(self, key: str, expires_sec: int = 3600) -> str:
        # Local files served via FastAPI static mount at /storage/
        return f"/storage/{key}"


class SeaweedFSEngine(BaseEngine):
    """S3-compatible SeaweedFS self-hosted object store.

    Wire by setting SEAWEEDFS_ENDPOINT (e.g. http://seaweedfs:8333),
    SEAWEEDFS_ACCESS_KEY, SEAWEEDFS_SECRET_KEY, SEAWEEDFS_BUCKET.
    """
    provider_id = "seaweedfs"
    display_name = "SeaweedFS (self-hosted S3-compatible)"
    capability = EngineCapability.STORAGE
    cost_hint = "Free (self-hosted)"
    hardware_hint = "1 CPU + 1GB RAM (single-node)"
    requires_key = True
    key_env_var = "SEAWEEDFS_ACCESS_KEY"

    def __init__(self) -> None:
        self.endpoint = os.getenv("SEAWEEDFS_ENDPOINT", "http://seaweedfs:8333")
        self.access_key = os.getenv("SEAWEEDFS_ACCESS_KEY", "admin")
        self.secret_key = os.getenv("SEAWEEDFS_SECRET_KEY", "secret")
        self.bucket = os.getenv("SEAWEEDFS_BUCKET", "content-factory")
        self._client = None

    def _s3(self):
        if self._client is None:
            try:
                import boto3  # type: ignore
            except ImportError as e:
                raise EngineError("boto3 not installed. `pip install boto3`.") from e
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
            try:
                self._client.create_bucket(Bucket=self.bucket)
            except Exception:
                pass  # bucket may already exist
        return self._client

    async def health(self) -> EngineHealth:
        try:
            s3 = self._s3()
            s3.head_bucket(Bucket=self.bucket)
            return EngineHealth(healthy=True, detail=f"endpoint={self.endpoint} bucket={self.bucket}")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        s3 = self._s3()
        s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return {"key": key, "size": len(data), "url": f"{self.endpoint}/{self.bucket}/{key}"}

    @engine_method
    def get(self, key: str) -> bytes:
        s3 = self._s3()
        obj = s3.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    @engine_method
    def delete(self, key: str) -> Dict[str, Any]:
        s3 = self._s3()
        s3.delete_object(Bucket=self.bucket, Key=key)
        return {"deleted": key}

    @engine_method
    def url(self, key: str, expires_sec: int = 3600) -> str:
        s3 = self._s3()
        return s3.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_sec
        )


class S3StorageEngine(BaseEngine):
    """AWS S3 backend. Delegates to the existing s3_uploader.py (no breaking changes)."""
    provider_id = "s3"
    display_name = "AWS S3 (legacy, optional)"
    capability = EngineCapability.STORAGE
    cost_hint = "AWS S3 pricing"
    hardware_hint = "cloud"
    requires_key = True
    key_env_var = "AWS_ACCESS_KEY_ID"

    def __init__(self) -> None:
        # Lazy: boto3 may not be installed in solo deployments that don't use S3.
        # We only require it in health()/put() when actually used.
        pass

    async def health(self) -> EngineHealth:
        try:
            from s3_uploader import get_s3_client  # type: ignore
            client = get_s3_client()
            client.list_buckets()
            return EngineHealth(healthy=True, detail="aws s3 reachable")
        except Exception as e:
            return EngineHealth(healthy=False, detail=f"{type(e).__name__}: {e}")

    @engine_method
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        from s3_uploader import upload_file_to_s3  # type: ignore
        url = upload_file_to_s3.__wrapped__ if hasattr(upload_file_to_s3, "__wrapped__") else None
        # Re-use the existing helper by writing a temp file then uploading
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(data)
            tmp_path = tf.name
        try:
            public_url = upload_file_to_s3(tmp_path, key)
        finally:
            os.remove(tmp_path)
        return {"key": key, "size": len(data), "url": public_url}

    @engine_method
    def get(self, key: str) -> bytes:
        raise EngineError("S3 storage get() not implemented via legacy helper; use s3_uploader.generate_presigned_url for direct downloads")

    @engine_method
    def delete(self, key: str) -> Dict[str, Any]:
        raise EngineError("S3 storage delete() not implemented via legacy helper; the s3_uploader keeps its own lifecycle")

    @engine_method
    def url(self, key: str, expires_sec: int = 3600) -> str:
        from s3_uploader import generate_presigned_url  # type: ignore
        return generate_presigned_url(key, expires_in=expires_sec)


def select_storage_engine() -> BaseEngine:
    """Pick the active storage engine based on STORAGE_BACKEND env var."""
    backend = os.getenv(STORAGE_BACKEND_ENV, "local").lower()
    if backend == "seaweedfs":
        return SeaweedFSEngine()
    if backend == "s3":
        return S3StorageEngine()
    return LocalStorageEngine()


__all__ = [
    "LocalStorageEngine",
    "SeaweedFSEngine",
    "S3StorageEngine",
    "select_storage_engine",
    "STORAGE_BACKEND_ENV",
    "LOCAL_STORAGE_DIR",
]
