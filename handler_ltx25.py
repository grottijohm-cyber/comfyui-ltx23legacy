"""RunPod entry point for the LTX 2.5 image-to-video worker."""
import runpod
from worker_ltx25 import handler

runpod.serverless.start({"handler": handler})
