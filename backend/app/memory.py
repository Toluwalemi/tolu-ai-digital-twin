from __future__ import annotations

import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

MAX_MESSAGES = 20

# In-memory fallback for local development (no GCS).
_local_store: dict[str, list[dict[str, str]]] = {}

# initialised GCS client.
_gcs_client = None
_gcs_bucket = None
_gcs_initialised = False


def _init_gcs() -> bool:
    """Initialise the GCS client once. Returns True if GCS is available."""
    global _gcs_client, _gcs_bucket, _gcs_initialised

    if _gcs_initialised:
        return _gcs_bucket is not None

    _gcs_initialised = True

    if not settings.gcs_bucket_name:
        logger.info("GCS_BUCKET_NAME not set — using in-memory conversation store.")
        return False

    try:
        from google.cloud import storage

        _gcs_client = storage.Client()
        _gcs_bucket = _gcs_client.bucket(settings.gcs_bucket_name)
        logger.info("GCS conversation memory initialised: %s", settings.gcs_bucket_name)
        return True
    except Exception:
        logger.warning("Failed to initialise GCS. Falling back to in-memory store.", exc_info=True)
        return False


def _blob_name(session_id: str) -> str:
    return f"conversations/{session_id}.json"


def load_history(session_id: str) -> list[dict[str, str]]:
    """Load conversation history for a session."""
    if _init_gcs():
        try:
            blob = _gcs_bucket.blob(_blob_name(session_id))
            if blob.exists():
                data = json.loads(blob.download_as_text())
                return data[-MAX_MESSAGES:]
        except Exception:
            logger.warning(
                "GCS read failed for %s — returning empty history.", session_id, exc_info=True
            )
        return []

    # In-memory fallback.
    return list(_local_store.get(session_id, []))[-MAX_MESSAGES:]


def save_history(session_id: str, messages: list[dict[str, str]]) -> None:
    """Persist conversation history for a session."""
    trimmed = messages[-MAX_MESSAGES:]

    if _init_gcs():
        try:
            blob = _gcs_bucket.blob(_blob_name(session_id))
            blob.upload_from_string(
                json.dumps(trimmed, ensure_ascii=False),
                content_type="application/json",
            )
            return
        except Exception:
            logger.warning(
                "GCS write failed for %s — saving in-memory only.", session_id, exc_info=True
            )

    # In-memory fallback.
    _local_store[session_id] = trimmed
