"""Webhook endpoint to notify clients when document processing completes."""
from __future__ import annotations
import json, os
from typing import Optional

try:
    import httpx
    _OK = True
except ImportError:
    _OK = False


def notify_completion(webhook_url: str, job_id: str, status: str, result: Optional[dict] = None, error: Optional[str] = None) -> bool:
    """
    POST a completion notification to a client webhook URL.
    Called by the worker after processing finishes (success or failure).
    """
    payload = {
        "event": "document.processed",
        "job_id": job_id,
        "status": status,
        "result": result,
        "error": error,
    }
    if not _OK or not webhook_url:
        print(f"[webhook] Would notify {webhook_url}: {payload}")
        return False
    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        return resp.status_code < 300
    except Exception as e:
        print(f"[webhook] Error notifying {webhook_url}: {e}")
        return False
