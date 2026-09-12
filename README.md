# LTX 2.5 image-to-video — RunPod Serverless

This branch is set up for the simplest deployment path:

- Deploy directly from this GitHub branch in RunPod.
- Select RunPod Cached Model: `Lightricks/LTX-2.5`.
- Use one 48 GB GPU.
- No Docker Desktop.
- No network volume.
- No local model downloads.
- API input is only `image` + `prompt`.
- The worker automatically expands the prompt with motion/camera/temporal-consistency guidance before generation.

## RunPod setup

1. In RunPod Serverless choose **Deploy from GitHub**.
2. Repository: `grottijohm-cyber/comfyui-ltx23legacy`.
3. Branch: `ltx25-cached`.
4. Dockerfile: `Dockerfile`.
5. Cached Model / Hugging Face model: `Lightricks/LTX-2.5`.
6. GPU: one 48 GB GPU (L40S / RTX 6000 Ada / RTX PRO 6000 class are suitable choices).
7. Active workers: 0.
8. Max workers: 1.
9. Idle timeout: 120 seconds.
10. Execution timeout: 7200 seconds.
11. Deploy.

RunPod's cached-model mount is expected at:
`/runpod-volume/huggingface-cache/hub/models--Lightricks--LTX-2.5/snapshots/<revision>/`

## Request format

```json
{
  "input": {
    "image": "https://example.com/image.jpg",
    "prompt": "The person turns toward the camera and smiles."
  }
}
```

`image` may be an HTTPS URL, a data URL, or raw base64 image data.

## Response

Successful jobs return the generated MP4 as base64:

```json
{
  "video": "<base64 mp4>",
  "mime_type": "video/mp4",
  "prompt_enhanced": true
}
```

## Generation defaults

- LTX 2.5 distilled official pipeline
- Image-to-video conditioning strength: 1.0
- 121 frames
- 24 fps (~5 seconds)
- 1216 × 704 output
- FP8 cast + CPU offload for practical 48 GB GPU use

The large LTX weights are not baked into the container. RunPod supplies them through Cached Models, which keeps the GitHub build much smaller.
