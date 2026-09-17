"""Generate high-quality SFW anchor portraits with LM Studio and ComfyUI.

Requirements:
  - LM Studio serving an OpenAI-compatible API on http://169.254.65.222:1234/v1
  - ComfyUI serving its API on http://127.0.0.1:8188
  - An SDXL checkpoint installed in ComfyUI/models/checkpoints

Environment variables:
  LM_STUDIO_URL      default: http://169.254.65.222:1234/v1
  COMFYUI_URL        default: http://127.0.0.1:8188
  COMFY_CHECKPOINT   default: sd_xl_base_1.0.safetensors
  ANCHOR_OUTPUT_DIR  default: ./agency/faces
"""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from pathlib import Path
from typing import Any

import requests


LM_STUDIO_URL = os.getenv(
    "LM_STUDIO_URL",
    "http://169.254.65.222:1234/v1",
).rstrip("/")
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
CHECKPOINT = os.getenv("COMFY_CHECKPOINT", "sd_xl_base_1.0.safetensors")
OUTPUT_DIR = Path(os.getenv("ANCHOR_OUTPUT_DIR", "./agency/faces"))
REQUEST_TIMEOUT = 30
GENERATION_TIMEOUT = 900

CHARACTER_SPECS = {
    "Aura_Vex": (
        "21-year-old digital-native woman, striking asymmetrical neon-violet eyes, "
        "shifting pastel hair color, smooth skin with a subtle digital shimmer texture, "
        "direct eye contact, modern studio ring-light reflection in the eyes"
    ),
    "Aria_Vance": (
        "24-year-old Scandinavian woman, sharp cheekbones, piercing blue eyes, "
        "blonde hair tied back, neutral outdoor studio lighting, elegant and elite look"
    ),
    "Kai_Cypher": (
        "26-year-old athletic male, sharp jawline, short cropped dark hair, "
        "modern minimalist background, focused and intelligent expression"
    ),
    "Lyra_Quant": (
        "28-year-old professional East Asian woman, stylish thin-rimmed glasses, "
        "dark hair pulled back into a neat bun, bright corporate studio background, confident look"
    ),
}

NEGATIVE_PROMPT = (
    "low quality, blurry, out of focus, illustration, cartoon, 3d render, CGI, "
    "side profile, turned head, closed eyes, crossed eyes, distorted face, asymmetrical face, "
    "extra fingers, bad hands, duplicate person, text, watermark, logo, harsh shadows"
)


def request_json(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
    response.raise_for_status()
    return response.json()


def get_lm_model() -> str:
    """Return the first model exposed by LM Studio."""
    payload = request_json("GET", f"{LM_STUDIO_URL}/models")
    models = payload.get("data", [])
    if not models:
        raise RuntimeError("LM Studio is running but has no loaded models.")
    return models[0]["id"]


def create_prompt(character_name: str, description: str, model: str) -> str:
    """Ask LM Studio for a detailed, portrait-focused generation prompt."""
    response = request_json(
        "POST",
        f"{LM_STUDIO_URL}/chat/completions",
        json={
            "model": model,
            "temperature": 0.35,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional photorealistic SDXL prompt engineer. "
                        "Return only one plain-text image prompt, with no markdown or commentary."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Create a prompt for {character_name}: {description}. "
                        "Make it a SFW high-resolution head-and-shoulders portrait, front-facing, "
                        "eye-level camera, direct eye contact, neutral expression, clean studio "
                        "background, soft even three-point lighting, realistic skin pores, natural "
                        "facial symmetry, crisp eyes, catchlights, professional editorial photography, "
                        "85mm portrait lens, shallow depth of field, centered composition."
                    ),
                },
            ],
        },
    )
    try:
        return response["choices"][0]["message"]["content"].strip().replace("```", "")
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected LM Studio response: {response}") from exc


def build_workflow(prompt: str, seed: int) -> dict[str, dict[str, Any]]:
    """Build a standard ComfyUI API-format SDXL workflow."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": CHECKPOINT},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE_PROMPT, "clip": ["1", 1]},
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": seed,
                "steps": 30,
                "cfg": 6.5,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0,
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "anchor", "images": ["6", 0]},
        },
    }


def generate_image(workflow: dict[str, dict[str, Any]]) -> tuple[str, str, str]:
    """Queue a workflow and return its prompt ID and saved image metadata."""
    client_id = str(uuid.uuid4())
    queued = request_json(
        "POST",
        f"{COMFYUI_URL}/prompt",
        json={"prompt": workflow, "client_id": client_id},
    )
    prompt_id = queued.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI did not return a prompt ID: {queued}")

    deadline = time.monotonic() + GENERATION_TIMEOUT
    while time.monotonic() < deadline:
        history = request_json("GET", f"{COMFYUI_URL}/history/{prompt_id}")
        item = history.get(prompt_id)
        if item and item.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"ComfyUI generation failed: {item['status']}")
        if item and item.get("outputs"):
            for output in item["outputs"].values():
                images = output.get("images", [])
                if images:
                    image = images[0]
                    return prompt_id, image["filename"], image.get("subfolder", "")
        time.sleep(2)

    raise TimeoutError(f"ComfyUI did not finish prompt {prompt_id} within {GENERATION_TIMEOUT}s.")


def download_image(filename: str, subfolder: str, destination: Path) -> None:
    response = requests.get(
        f"{COMFYUI_URL}/view",
        params={"filename": filename, "subfolder": subfolder, "type": "output"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    destination.write_bytes(response.content)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    request_json("GET", f"{COMFYUI_URL}/system_stats")
    model = get_lm_model()
    print(f"Using LM Studio model: {model}")
    print(f"Using ComfyUI checkpoint: {CHECKPOINT}")

    for character_name, description in CHARACTER_SPECS.items():
        print(f"\n[{character_name}] Creating detailed prompt...")
        detailed_prompt = create_prompt(character_name, description, model)
        seed = random.randint(0, 2**32 - 1)
        print(f"[{character_name}] Queueing SDXL render with seed {seed}...")
        _, filename, subfolder = generate_image(build_workflow(detailed_prompt, seed))
        destination = OUTPUT_DIR / f"{character_name}_anchor.png"
        download_image(filename, subfolder, destination)
        print(f"[{character_name}] Saved {destination}")


if __name__ == "__main__":
    main()
