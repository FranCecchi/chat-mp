import json
from typing import Any

import aiohttp
import modal

vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.21.0")
    .env(
        {
            "HF_XET_HIGH_PERFORMANCE": "1",  # faster model transfers
            "VLLM_LOG_STATS_INTERVAL": "1",  # more frequent metrics logging
        }
    )
)

# 2. Modelo
MODEL_NAME = "google/gemma-4-E4B-it" #MODEL_NAME = "google/gemma-4-4b-it"
MODEL_REVISION = "d6436b3d62967e1af08bbb046c6300b2a9ae8e85"  

# 3. Volúmenes de caché
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

FAST_BOOT = True  # True para pruebas, False para producción

# 4. Configuración de arranque y speculative decoding
# Speculative decoding: NO lo usamos para el modelo 4B
# No es necesario y agrega complejidad innecesaria en esta etapa
SPECULATIVE_MODEL_NAME = None
SPECULATIVE_MODEL_REVISION = None

app = modal.App("educeva-chatbot")  # nombre de tu proyecto

N_GPU = 1
MINUTES = 60  # seconds
VLLM_PORT = 8000


@app.function(
    image=vllm_image,
    gpu="L4:1",
    scaledown_window=7 * MINUTES,  # how long should we stay up with no requests?
    timeout=10 * MINUTES,  # how long should we wait for container start?
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
    secrets=[modal.Secret.from_name("my-huggingface-secret")],  
)
@modal.concurrent(  # how many requests can one replica handle? tune carefully!
    max_inputs=30,
)
@modal.web_server(port=VLLM_PORT, startup_timeout=10 * MINUTES)
def serve():
    import json
    import subprocess

    cmd = [
        "vllm",
        "serve",
        MODEL_NAME,
        "--revision",
        MODEL_REVISION,
        "--served-model-name",
        MODEL_NAME,
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--uvicorn-log-level=info",
        "--async-scheduling",
    ]

    # enforce-eager disables both Torch compilation and CUDA graph capture
    # default is no-enforce-eager. see the --compilation-config flag for tighter control
    cmd += ["--enforce-eager" if FAST_BOOT else "--no-enforce-eager"]

    # assume multiple GPUs are for splitting up large matrix multiplications
    cmd += ["--tensor-parallel-size", str(N_GPU)]

    # Modelo de solo texto: no necesita flags multimodal ni tool-calling

    if SPECULATIVE_MODEL_NAME:
        cmd += [
            "--speculative-config",
            json.dumps({
                "model": SPECULATIVE_MODEL_NAME,
                "revision": SPECULATIVE_MODEL_REVISION,
                "num_speculative_tokens": 4
            }),
        ]

    print(*cmd)

    subprocess.Popen(cmd)  # sin shell=True, más seguro y correcto con lista
