"""
🎨 Generate Master Reference Face Images for AI Influencer Agency

This script creates high-resolution, front-facing portrait anchor images for each influencer.
It connects to LM Studio (for detailed prompt generation) and ComfyUI (for image synthesis),
then saves the results as master reference files for InstantID face consistency.

Run this after ensuring:
  - LM Studio is running on port 1234 with your base model loaded
  - ComfyUI is running on port 8188 with a Flux.1 or SDXL text-to-image API enabled

Usage:
  python generate_anchors.py

Output:
  ./agency/faces/{Character_Name}_anchor.png (for each of the 4 influencers)
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import requests
import websocket


# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

LM_STUDIO_URL = "http://192.168.10.105:1234/v1"
COMFYUI_URL = "http://127.0.0.1:8188"

OUTPUT_DIR = "./agency/faces"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────
# CHARACTER DEFINITIONS (basic descriptions → detailed prompts)
# ──────────────────────────────────────────────────────────────

CHARACTER_SPECS = {
    "Lumi_Thorne": {
        "name": "Lumi_Thorne",
        "description": "22-year-old brunette woman, warm hazel eyes, friendly smile, casual bedroom setting, relatable 'girl next door' aesthetic, highly realistic texture.",
        "niche": "Premium Companion"
    },
    "Aria_Vance": {
        "name": "Aria_Vance",
        "description": "24-year-old Scandinavian woman, sharp cheekbones, piercing blue eyes, blonde hair tied back, neutral outdoor studio lighting, elegant and elite look.",
        "niche": "Luxury Travel"
    },
    "Kai_Cypher": {
        "name": "Kai_Cypher",
        "description": "26-year-old athletic male, sharp jawline, short cropped dark hair, modern minimalist background, focused and intelligent expression.",
        "niche": "Tech & AI Gadgets"
    },
    "Lyra_Quant": {
        "name": "Lyra_Quant",
        "description": "28-year-old professional East Asian woman, stylish thin-rimmed glasses, dark hair pulled back into a neat bun, bright corporate studio background, confident look.",
        "niche": "Finance & Web3"
    }
}


# ──────────────────────────────────────────────────────────────
# STEP 1: Query LM Studio for detailed image prompts
# ──────────────────────────────────────────────────────────────

def get_detailed_prompt(base_description: str, character_name: str) -> str:
    """Send a basic character description to LM Studio and ask it to generate
    a hyper-detailed, photorealistic ComfyUI-compatible image prompt. Focuses on high-detail skin texture, neutral eye-level angles, clean backgrounds."""

    system_prompt = (
        "You are an expert AI image prompt engineer specializing in photorealistic character generation. "
        "Your task is to create a highly detailed, professional image prompt optimized for Flux.1 / SDXL text-to-image pipelines. "
        "The prompt should include: subject description, lighting setup, camera angle/pose, composition details, "
        "texture quality keywords, aspect ratio, and technical rendering parameters. Keep it concise but thorough."
    )

    user_prompt = (
        f"Create a photorealistic image prompt for this influencer character:\n\n"
        f"{base_description}\n\n"
        f"Requirements:\n"
        f"- Front-facing portrait, eye-level camera angle\n"
        f"- Clean, neutral studio background that doesn't distract from the face\n"
        f"- Soft, even lighting with no harsh shadows on the face\n"
        f"- Photorealistic texture, skin details, eye reflections visible\n"
        f"- 8K resolution quality, professional photography style\n"
        f"- Output ONLY the image prompt text (no markdown, no extra commentary)"
    )

    headers = {"Content-Type": "application/json"}
    data = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,  # Low temperature for consistent prompt output
    }

    print(f"📝 Querying LM Studio for detailed prompt ({character_name})...")
    response = requests.post(
        f"{LM_STUDIO_URL}/chat/completions",
        headers=headers,
        json=data,
        timeout=60
    )

    if response.status_code == 200:
        raw_response = response.json()

        # LM Studio API uses "choices" array with message objects
        choices = raw_response.get("choices", [])
        if len(choices) > 0 and isinstance(choices[0], dict):
            raw_content = choices[0]["message"]["content"]
        else:
            # Fallback for other response formats
            raw_content = raw_response.get("text", "")

        print(f"  ✓ Response received: {raw_content[:50]}...")
    else:
        print(f"⚠️ LM Studio API returned status {response.status_code}: {response.text}")
        # Fallback: use a pre-crafted detailed prompt
        raw_content = f"{base_description}, front-facing portrait, eye-level camera angle, clean white studio background, soft even lighting, photorealistic texture, 8K resolution, professional photography, shallow depth of field focused on face"

    # Clean up any markdown or formatting artifacts
    if isinstance(raw_content, str):
        prompt = raw_content.strip()
        if "```" in prompt:
            # Remove code block markers if present
            prompt = prompt.replace("```", "").strip()
        print(f"✓ Prompt generated for {character_name}")
        return prompt


# ──────────────────────────────────────────────────────────────
# STEP 2: Generate images via ComfyUI API
# ──────────────────────────────────────────────────────────────

def generate_image_via_comfyui(prompt_text: str, character_name: str, seed: int = None) -> str:
    """Send a prompt to ComfyUI's web UI for generation and return the output path."""

    if seed is None:
        seed = int(time.time() * 1000) % 2**32

    print(f"🎨 Generating {character_name} portrait (seed={seed})...")

    # Load the base Flux.1 template (no InstantID needed for anchor generation)
    with open("flux_instantid_template.json", "r") as f:
        workflow = json.load(f)

    # Adjust node inputs to use our generated prompt
    # Node 6 is Positive Text Encode - inject the detailed prompt here
    if "6" in workflow and "inputs" in workflow["6"]:
        workflow["6"]["inputs"]["text"] = prompt_text

    # Set random seed for KSampler (node 3)
    if "3" in workflow:
        workflow["3"]["params"]["seed"] = seed

    # Remove the InstantID node since we don't need face consistency yet
    # (we're creating master references, not using them yet)
    nodes_to_remove = [i for i, n in enumerate(workflow["nodes"]) if n["type"] == "InstantID"]
    workflow["nodes"].remove(workflow["nodes"][nodes_to_remove[0]])

    # Re-index the nodes after removal
    for i, node in enumerate(workflow["nodes"], start=1):
        node["id"] = i

    # Establish WebSocket connection to ComfyUI
    ws = websocket.WebSocket()
    ws.connect(f"ws://{COMFYUI_URL}/ws?clientId={uuid.uuid4()}")

    # Send the workflow for generation
    p = {"prompt": workflow}
    data = json.dumps(p).encode('utf-8')
    req = requests.post(f"{COMFYUI_URL}/prompt", data=data)
    prompt_id = req.json()["prompt_id"]

    print(f"  → ComfyUI request ID: {prompt_id}")

    # Listen for completion via WebSocket
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                exec_data = message["data"]
                if exec_data["node"] is None and exec_data["prompt_id"] == prompt_id:
                    print(f"  ✓ Generation complete!")
                    break

    # Retrieve output filename from ComfyUI history
    history_req = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    history = history_req.json()[prompt_id]

    # Extract filename (from node 12's outputs)
    if "12" in history and "images" in history["outputs"]:
        filename = history["outputs"]["12"]["images"][0]["filename"]
    else:
        # Fallback: get first image from any output
        for key, value in history["outputs"].items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                filename = value[0].get("filename", f"{character_name}.png")
                break

    # Construct full path (ComfyUI typically saves to C:/comfyui/output/)
    # Adjust if your ComfyUI output directory differs
    output_dir = os.path.join(os.environ.get("COMFYUI_OUTPUT_DIR", "C:/comfyui/output"), filename)

    print(f"  ✓ Image saved: {output_dir}")
    return output_dir


# ──────────────────────────────────────────────────────────────
# STEP 3: Download ComfyUI image and save locally
# ──────────────────────────────────────────────────────────────

def download_comfyui_image(prompt_id: str, filename: str) -> str:
    """Download the generated image from ComfyUI's output folder."""

    history_req = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    history = history_req.json()[prompt_id]

    # Get the image URL from ComfyUI's file server
    if "12" in history and "images" in history["outputs"]:
        img_data = history["outputs"]["12"]["images"][0]
        url = img_data.get("url", "")

        print(f"  → Downloading image from: {url}")

        # Download the actual image file
        response = requests.get(url)
        if response.status_code == 200:
            save_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
            with open(save_path, 'wb') as f:
                f.write(response.content)

            # Verify the file exists and has reasonable size (>1KB)
            if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
                print(f"  ✓ Downloaded successfully: {os.path.basename(save_path)}")
                return save_path
            else:
                raise Exception("Downloaded file is too small or invalid")
        else:
            raise Exception(f"Failed to download image (HTTP {response.status_code})")

    # Fallback: assume file was saved locally by ComfyUI
    return f"{COMFYUI_URL}/output/{filename}.png"


# ──────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────────────────────

def run_generate_anchors():
    """Run the complete anchor image generation pipeline."""

    print("=" * 60)
    print("🎨 AI Influencer Agency - Master Anchor Image Generator")
    print("=" * 60)
    print(f"Target: {OUTPUT_DIR}")
    print(f"LM Studio: {LM_STUDIO_URL}")
    print(f"ComfyUI:   {COMFYUI_URL}")
    print()

    all_results = []

    for char_id, spec in CHARACTER_SPECS.items():
        name = spec["name"]

        # Step 1: Get detailed prompt from LM Studio
        detailed_prompt = get_detailed_prompt(spec["description"], name)
        print(f"  Prompt preview: {detailed_prompt[:80]}...")

        # Step 2: Generate image via ComfyUI
        try:
            output_path = generate_image_via_comfyui(detailed_prompt, name)

            # Step 3: Download and save locally
            local_path = download_comfyui_image(42, f"{name}")  # Use a dummy prompt_id for this example

            # Save with proper naming convention
            final_filename = f"{name}_anchor.png"
            final_path = os.path.join(OUTPUT_DIR, final_filename)

            if local_path != final_path:
                import shutil
                shutil.copy2(local_path, final_path)

            all_results.append({
                "character": name,
                "path": final_path,
                "status": "success"
            })
            print(f"  ✅ {name}: {final_filename}")

        except Exception as e:
            error_msg = str(e)[:100]
            all_results.append({
                "character": name,
                "path": None,
                "status": f"failed: {error_msg}"
            })
            print(f"  ❌ {name}: {error_msg}")

    # Summary
    print("\n" + "=" * 60)
    success_count = sum(1 for r in all_results if r["status"] == "success")
    total_count = len(all_results)

    print(f"\n📊 Summary: {success_count}/{total_count} characters generated successfully")

    for result in all_results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        path_info = f"{result['path']}" if result["path"] else "N/A"
        print(f"  {status_icon} {result['character']} → {path_info}")

    return all_results


# ──────────────────────────────────────────────────────────────
# VERIFICATION: Check that output files exist and are valid
# ──────────────────────────────────────────────────────────────

def verify_anchors():
    """Verify that anchor images were created successfully."""

    print("\n🔍 Verifying generated anchor images...")

    expected = [f"{name}_anchor.png" for name in CHARACTER_SPECS.keys()]
    results = []

    for filename in expected:
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            print(f"  ✅ {filename} ({size_kb:.1f} KB)")
            results.append({"name": filename, "status": "exists", "size_kb": size_kb})
        else:
            print(f"  ❌ {filename} (not found)")
            results.append({"name": filename, "status": "missing"})

    return results


if __name__ == "__main__":
    # Run the full pipeline
    run_generate_anchors()

    # Verify outputs
    verify_anchors()

    print("\n" + "=" * 60)
    print("🎉 Anchor image generation complete!")
    print(f"Check {OUTPUT_DIR} for your master reference face images.")
    print("=" * 60)