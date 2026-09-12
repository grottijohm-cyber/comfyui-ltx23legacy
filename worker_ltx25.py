"""Minimal RunPod adapter for LTX 2.5 image-to-video.

Public API stays intentionally tiny: {"input": {"image": ..., "prompt": ...}}
The worker validates/normalizes the image and prompt and hands them to the
bundled ComfyUI service. The actual Comfy graph is selected through the native
LTX 2.5 image-to-video template available in current ComfyUI.
"""
from __future__ import annotations

import base64
import io
import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image

COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188").rstrip("/")
TIMEOUT = int(os.getenv("JOB_TIMEOUT_SECONDS", "7200"))
INPUT_DIR = Path("/comfyui/input")


def _image_bytes(value: str) -> bytes:
    if value.startswith("data:"):
        value = value.split(",", 1)[1]
    if value.startswith(("http://", "https://")):
        r = requests.get(value, timeout=60)
        r.raise_for_status()
        return r.content
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError("image must be a URL, data URL, or base64 string") from exc


def _save_image(value: str) -> str:
    raw = _image_bytes(value)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    name = f"ltx25-{uuid.uuid4().hex}.png"
    img.save(INPUT_DIR / name, "PNG")
    return name


def _wait_comfy() -> None:
    deadline = time.time() + 900
    while time.time() < deadline:
        try:
            if requests.get(f"{COMFY_URL}/system_stats", timeout=5).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError("ComfyUI did not become ready")


def handler(job):
    data = job.get("input") or {}
    image = data.get("image")
    prompt = str(data.get("prompt") or "").strip()
    if not image or not prompt:
        return {"error": "Provide exactly image + prompt."}

    _wait_comfy()
    image_name = _save_image(image)

    # Current ComfyUI exposes the official LTX 2.5 Image-to-Video blueprint as a
    # native template. This adapter deliberately keeps user input to two fields.
    # A deployment-time smoke test must export that template to API JSON before
    # this branch is promoted to main.
    return {
        "error": "LTX25_API_WORKFLOW_NOT_EXPORTED",
        "message": "Container and model mapping are ready; export the official LTX 2.5 Image-to-Video template to API JSON before production deployment.",
        "image_file": image_name,
        "prompt": prompt,
    }
