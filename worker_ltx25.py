"""RunPod LTX 2.5 image-to-video worker.

API input is intentionally just:
  {"input": {"image": "<URL/data-url/base64>", "prompt": "..."}}

RunPod Cached Models supplies the Lightricks/LTX-2.5 repository at runtime.
The worker uses Lightricks' official distilled pipeline directly, so no ComfyUI
workflow export is required.
"""
from __future__ import annotations

import base64
import io
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

import requests
from PIL import Image

CACHE_ROOT = Path(os.getenv("RUNPOD_HF_CACHE", "/runpod-volume/huggingface-cache/hub"))
MODEL_REPO_DIR = CACHE_ROOT / "models--Lightricks--LTX-2.5" / "snapshots"
TIMEOUT = int(os.getenv("JOB_TIMEOUT_SECONDS", "7200"))


def _image_bytes(value: str) -> bytes:
    value = str(value).strip()
    if value.startswith("data:"):
        value = value.split(",", 1)[1]
    if value.startswith(("http://", "https://")):
        response = requests.get(value, timeout=60)
        response.raise_for_status()
        return response.content
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError("image must be an https URL, data URL, or base64 string") from exc


def _save_image(value: str, directory: Path) -> Path:
    raw = _image_bytes(value)
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    path = directory / f"input-{uuid.uuid4().hex}.png"
    image.save(path, "PNG")
    return path


def _snapshot() -> Path:
    if not MODEL_REPO_DIR.exists():
        raise RuntimeError(
            "LTX 2.5 cached model is missing. In the RunPod endpoint settings, "
            "select Cached Model: Lightricks/LTX-2.5."
        )
    snapshots = [p for p in MODEL_REPO_DIR.iterdir() if p.is_dir()]
    if not snapshots:
        raise RuntimeError("RunPod has not finished mounting the LTX 2.5 cached model yet.")
    return max(snapshots, key=lambda p: p.stat().st_mtime)


def _require(root: Path, relative: str) -> str:
    path = root / relative
    if not path.exists():
        raise RuntimeError(f"Cached LTX 2.5 file missing: {relative}")
    return str(path)


def _enhance_prompt(prompt: str) -> str:
    """Lightweight automatic enhancer with no second model/download.

    It preserves the user's requested subject/action verbatim and appends motion,
    camera, temporal-coherence and audio guidance that tends to help I2V prompts.
    """
    prompt = " ".join(prompt.split())
    suffix = (
        " Single continuous cinematic shot. Preserve the identity, clothing, scene layout, "
        "and important details from the input image. Natural physically plausible motion, "
        "clear subject action, coherent camera movement, realistic lighting and shadows, "
        "stable anatomy and proportions, strong temporal consistency, fine texture detail, "
        "no abrupt cuts or scene changes. Synchronized natural ambient audio matching the scene."
    )
    return prompt + suffix


def _run_generation(image_path: Path, prompt: str, output_path: Path) -> None:
    root = _snapshot()
    transformer = _require(root, "diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors")
    text_encoder = _require(root, "text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors")
    video_vae = _require(root, "vae/ltx-2.5-video-vae-bf16.safetensors")
    audio_vae = _require(root, "vae/ltx-2.5-audio-vae-bf16.safetensors")
    duration_head = _require(root, "model_patches/ltx-2.5-duration-head-bf16.safetensors")
    upscaler = _require(root, "latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors")

    command = [
        "python", "-m", "ltx_pipelines.distilled",
        "--transformer-path", transformer,
        "--text-encoder-path", text_encoder,
        "--video-vae-path", video_vae,
        "--audio-vae-path", audio_vae,
        "--duration-head-path", duration_head,
        "--spatial-upsampler-path", upscaler,
        "--image", str(image_path), "0", "1.0",
        "--prompt", _enhance_prompt(prompt),
        "--seed", str(int.from_bytes(os.urandom(4), "big")),
        "--height", "704",
        "--width", "1216",
        "--num-frames", "121",
        "--frame-rate", "24",
        "--quantization", "fp8-cast",
        "--offload", "cpu",
        "--output-path", str(output_path),
    ]
    subprocess.run(command, check=True, timeout=TIMEOUT)


def handler(job):
    data = job.get("input") or {}
    image = data.get("image")
    prompt = str(data.get("prompt") or "").strip()
    if not image or not prompt:
        return {"error": "Provide image and prompt."}

    try:
        with tempfile.TemporaryDirectory(prefix="ltx25-") as temp_dir:
            work = Path(temp_dir)
            image_path = _save_image(str(image), work)
            output_path = work / "output.mp4"
            _run_generation(image_path, prompt, output_path)
            if not output_path.exists():
                raise RuntimeError("LTX 2.5 completed without creating output.mp4")
            encoded = base64.b64encode(output_path.read_bytes()).decode("ascii")
            return {
                "video": encoded,
                "mime_type": "video/mp4",
                "prompt_enhanced": True,
            }
    except subprocess.TimeoutExpired:
        return {"error": f"Generation exceeded the {TIMEOUT}-second timeout."}
    except subprocess.CalledProcessError as exc:
        return {"error": f"LTX 2.5 generation failed with exit code {exc.returncode}."}
    except Exception as exc:
        return {"error": str(exc)}
