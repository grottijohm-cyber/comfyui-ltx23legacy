# clean base image containing only comfyui, comfy-cli and comfyui-manager
FROM runpod/worker-comfyui:5.10.0-base

# build-time tokens for gated downloads — never baked into final image.
# pass via: docker build --build-arg HF_TOKEN=$HF_TOKEN ...
ARG HF_TOKEN=""

# install custom nodes into comfyui
RUN comfy node install --exit-on-fail cg-use-everywhere@7.5.2 --mode remote || (echo "WARN: cg-use-everywhere@7.5.2 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail cg-use-everywhere --mode remote)
RUN comfy node install --exit-on-fail comfyui-impact-pack@8.28.2 || (echo "WARN: comfyui-impact-pack@8.28.2 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail comfyui-impact-pack)
RUN comfy node install --exit-on-fail comfyui-easy-use@1.3.6 || (echo "WARN: comfyui-easy-use@1.3.6 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail comfyui-easy-use)
RUN comfy node install --exit-on-fail comfyui-kjnodes@1.4.2 || (echo "WARN: comfyui-kjnodes@1.4.2 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail comfyui-kjnodes)
RUN comfy node install --exit-on-fail comfyui-melbandroformer@1.0.1 || (echo "WARN: comfyui-melbandroformer@1.0.1 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail comfyui-melbandroformer)
RUN comfy node install --exit-on-fail rgthree-comfy@1.0.2605082257 || (echo "WARN: rgthree-comfy@1.0.2605082257 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail rgthree-comfy)
RUN comfy node install --exit-on-fail comfyui-custom-scripts@1.2.5 || (echo "WARN: comfyui-custom-scripts@1.2.5 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail comfyui-custom-scripts)
RUN git clone https://github.com/Lightricks/ComfyUI-LTXVideo /comfyui/custom_nodes/ComfyUI-LTXVideo && cd /comfyui/custom_nodes/ComfyUI-LTXVideo && (git checkout 531512f7286963dc7aff1fd8bf5556e95eae03af 2>/dev/null || (git fetch origin 531512f7286963dc7aff1fd8bf5556e95eae03af --depth=1 && git checkout 531512f7286963dc7aff1fd8bf5556e95eae03af) || echo "WARN: commit 531512f7286963dc7aff1fd8bf5556e95eae03af unreachable in https://github.com/Lightricks/ComfyUI-LTXVideo, falling back to default branch HEAD")
RUN uv pip install -r /comfyui/custom_nodes/ComfyUI-LTXVideo/requirements.txt
RUN comfy node install --exit-on-fail crt-nodes@2.4.9 || (echo "WARN: crt-nodes@2.4.9 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail crt-nodes)
RUN comfy node install --exit-on-fail comfyui-resolution-master@1.6.0 || (echo "WARN: comfyui-resolution-master@1.6.0 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail comfyui-resolution-master)
RUN comfy node install --exit-on-fail comfyui-videohelpersuite@1.7.9 || (echo "WARN: comfyui-videohelpersuite@1.7.9 unavailable in registry, falling back to latest" >&2 && comfy node install --exit-on-fail comfyui-videohelpersuite)

# download models into comfyui
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/diffusion_models/ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled.safetensors' --relative-path models/diffusion_models --filename 'ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/vae/LTX23_video_vae_bf16.safetensors' --relative-path models/vae --filename 'LTX23_video_vae_bf16.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/Kijai/LTX2.3_comfy/resolve/main/vae/LTX23_audio_vae_bf16.safetensors' --relative-path models/vae --filename 'LTX23_audio_vae_bf16.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/Kijai/MelBandRoFormer_comfy/resolve/main/MelBandRoformer_fp16.safetensors' --relative-path models/diffusion_models --filename 'MelBandRoformer_fp16.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/AviadDahan/LTX-2.3-ID-LoRA-CelebVHQ-3K/resolve/main/lora_weights.safetensors' --relative-path models/loras --filename 'LTX2.3/LTX-2_3-ID-LoRA-CelebVHQ-3K.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-spatial-upscaler-x2-1.1.safetensors' --relative-path models/latent_upscale_models --filename 'ltx-2.3-spatial-upscaler-x2-1.1.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control/resolve/main/ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors' --relative-path models/loras --filename 'LTX2.3/ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/Lightricks/LTX-2-19b-IC-LoRA-Detailer/resolve/main/ltx-2-19b-ic-lora-detailer.safetensors' --relative-path models/loras --filename 'LTX2/ltx-2-19b-ic-lora-detailer.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp8_scaled.safetensors' --relative-path models/text_encoders --filename 'gemma_3_12B_it_fp8_scaled.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done
RUN BACKOFFS="10 20 30 60 90" && for i in 1 2 3 4 5; do HF_TOKEN=$HF_TOKEN comfy model download --url 'https://huggingface.co/ReubenF10/ComfyUI-Models/resolve/main/text_encoders/ltx-2.3_text_projection_bf16.safetensors' --relative-path models/text_encoders --filename 'ltx-2.3_text_projection_bf16.safetensors' && break; if [ $i -eq 5 ]; then echo "model-download failed after 5 attempts" >&2; exit 1; fi; SLEEP=$(echo $BACKOFFS | cut -d ' ' -f $i) && echo "model-download attempt $i failed; retrying in $SLEEP seconds" >&2; sleep $SLEEP; done

# Install the thin image-only RunPod handler over the base image's generic
# "send the entire workflow" handler. The inherited /start.sh starts ComfyUI
# and then executes /handler.py.
RUN mkdir -p /app
COPY requirements.txt /app/requirements.txt
RUN uv pip install -r /app/requirements.txt
COPY api-workflow.json /app/api-workflow.json
COPY handler.py worker.py /

ENV WORKFLOW_PATH=/app/api-workflow.json \
    COMFY_URL=http://127.0.0.1:8188 \
    JOB_TIMEOUT_SECONDS=7200
