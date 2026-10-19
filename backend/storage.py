
import os
from io import BytesIO
from pathlib import Path

from google.cloud import storage


CLOUD_MODE = os.getenv("CLOUD_MODE", "false").lower() == "true"

BUCKET_NAME = os.getenv(
    "GCS_BUCKET_NAME",
    "mediclaim-claims-509016"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
LOCAL_UPLOAD_DIR = PROJECT_DIR / "uploads"

_storage_client = None


def get_storage_client():
    global _storage_client

    if _storage_client is None:
        _storage_client = storage.Client()

    return _storage_client


def save_claim_file(filename: str, content: bytes) -> str:
    """Save an uploaded claim and return its durable location."""

    if CLOUD_MODE:
        client = get_storage_client()
        bucket = client.bucket(BUCKET_NAME)

        object_name = f"claims/{filename}"
        blob = bucket.blob(object_name)

        blob.upload_from_file(
            BytesIO(content),
            content_type="application/pdf"
        )

        return f"gs://{BUCKET_NAME}/{object_name}"

    LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_path = LOCAL_UPLOAD_DIR / filename
    file_path.write_bytes(content)

    return str(file_path)


def read_claim_file(file_path: str) -> bytes:
    """Read a claim from Cloud Storage or local storage."""

    if file_path.startswith("gs://"):
        client = get_storage_client()

        bucket_name, object_name = (
            file_path[5:].split("/", 1)
        )

        blob = client.bucket(bucket_name).blob(object_name)

        return blob.download_as_bytes()

    # Supports historical local uploads during migration.
    return Path(file_path).read_bytes()
