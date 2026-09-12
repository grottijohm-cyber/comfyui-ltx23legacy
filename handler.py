"""RunPod Serverless entrypoint."""

import runpod

from worker import handle_job


if __name__ == "__main__":
    runpod.serverless.start({"handler": handle_job})

