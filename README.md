# LTX 2.3 image-to-video — RunPod Serverless

This repository packages the LTX 2.3 Legacy ComfyUI workflow as a fixed,
queue-based RunPod Serverless worker. A request supplies one image; the worker
uploads it to ComfyUI, inserts it into node `350`, runs the bundled workflow,
and returns the MP4 produced by node `449`.

The client never sends a workflow, prompt, seed, or ComfyUI node mapping.

## Request

Use `/run` for this long-running video job:

```bash
curl --request POST \
  "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run" \
  --header "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "input": {
      "image": "https://example.com/reference.png"
    }
  }'
```

`input.image` may be an HTTP(S) URL, a base64 string, or a base64 data URI:

```json
{
  "input": {
    "image": "data:image/png;base64,iVBORw0KGgo..."
  }
}
```

No other input fields are accepted.

## Response

With S3-compatible storage configured:

```json
{
  "status": "success",
  "prompt_id": "...",
  "videos": [
    {
      "filename": "LTX2_3_00001-audio.mp4",
      "type": "url",
      "url": "https://...",
      "mime_type": "video/mp4"
    }
  ]
}
```

Without object storage, outputs up to 8 MiB are returned as base64. Larger
outputs return an error explaining which storage variables are missing.

## Deploy from GitHub

1. Commit and push these files to the repository's `main` branch.
2. In RunPod, create a **Serverless → Queue** endpoint.
3. Choose **Deploy from GitHub**, select this repository and `Dockerfile`.
4. Choose a GPU with enough VRAM for the LTX 2.3 22B workflow.
5. Set the endpoint execution timeout to at least `7200` seconds.
6. Deploy, then submit the request shown above.

The Docker build downloads the workflow's model weights. The first build is
large. `HF_TOKEN` can be supplied as a build argument if Hugging Face requires
authentication.

## Output storage

Video output is normally too large to place directly in a RunPod job response.
Configure these endpoint environment variables for any S3-compatible provider:

```text
BUCKET_ENDPOINT_URL=https://s3.REGION.amazonaws.com
BUCKET_ACCESS_KEY_ID=...
BUCKET_SECRET_ACCESS_KEY=...
BUCKET_NAME=your-bucket
```

The credentials stay in RunPod environment variables and must not be committed
to this repository.

## Important files

- `handler.py` starts the RunPod queue handler.
- `worker.py` validates/downloads the image, runs ComfyUI, and publishes output.
- `api-workflow.json` is the repaired Keyframe 1 API workflow.
- `workflow.json` is the editable ComfyUI canvas workflow.
- `Dockerfile` installs ComfyUI nodes, models, and the image-only handler.

## Local structural tests

These tests do not load the LTX models or require a GPU:

```bash
python -m unittest discover -s tests -v
```
