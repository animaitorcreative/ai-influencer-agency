import os
import json
import time
import requests
import websocket
import schedule
import uuid
from datetime import datetime

# --- CONFIGURATION ---
LM_STUDIO_URL = "http://192.168.10.105:1234/v1/chat/completions"
COMFYUI_URL = "127.0.0.1:8188"
BUFFER_API_URL = "https://bufferapp.com"
BUFFER_ACCESS_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")

# Imgur API configuration for public image hosting
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "")
IMGUR_UPLOAD_ENDPOINT = f"https://api.imgur.com/3/image?client_id={IMGUR_CLIENT_ID}"

INFLUENCERS = {
    "Aria_Vance": {
        "niche": "Luxury Travel & Lifestyle",
        "system_prompt": "You are Aria Vance, a luxury travel influencer. Generate a highly engaging 30-second Reel script/caption about an elite travel destination. Output format MUST be a single, strict, valid JSON object containing exactly two keys: 'caption' and 'image_prompt'. Your image_prompt must describe a high-end luxury lifestyle scene, 8k, incorporating a 24-year-old Scandinavian woman with sharp cheekbones and hazel eyes.",
        "buffer_profile_ids": ["INSTAGRAM_PROFILE_ID_1", "TIKTOK_PROFILE_ID_1"],
        "fixed_seed": 420691337
    },
    "Kai_Cypher": {
        "niche": "Tech, AI & Gadgets",
        "system_prompt": "You are Kai Cypher, an edgetech reviewer. Generate a short script/caption breaking down a futuristic desk setup or tech wearable. Output format MUST be a single, strict, valid JSON object containing exactly two keys: 'caption' and 'image_prompt'. Your image_prompt must describe a cyberpunk minimalist tech aesthetic, macro lens photography, incorporating a 26-year-old athletic male character with a sharp jawline and short cropped dark hair.",
        "buffer_profile_ids": ["INSTAGRAM_PROFILE_ID_2", "TIKTOK_PROFILE_ID_2"],
        "fixed_seed": 777123999
    },
    "Lyra_Quant": {
        "niche": "Personal Finance & Web3",
        "system_prompt": "You are Lyra Quant, a fintech consultant. Generate an analytical breakdown/caption regarding algorithmic trading concepts or personal finance hacks. Output format MUST be a single, strict, valid JSON object containing exactly two keys: 'caption' and 'image_prompt'. Your image_prompt must describe a clean office or bright corporate backdrop, modern data visualization overlays, incorporating a 28-year-old professional woman with glasses and dark brown hair pulled back.",
        "buffer_profile_ids": ["INSTAGRAM_PROFILE_ID_3", "X_PROFILE_ID_3"],
        "fixed_seed": 888999111
    }
}

# --- MONETIZATION LAYER: Premium Services ---
class MonetizationEngine:
    """High-ticket monetization for rapid revenue generation."""
    
    @staticmethod
    def calculate_post_value(influencer_name, content_quality):
        """Calculate potential revenue per post based on niche and quality."""
        value_matrix = {
            "Aria_Vance": {"base": 2000, "premium": 5000},  # Luxury/Lifestyle - high CPM
            "Kai_Cypher": {"base": 1500, "premium": 4000},   # Tech/AI - strong advertiser demand
            "Lyra_Quant": {"base": 2500, "premium": 6000}    # Finance/Web3 - premium niche
        }
        
        matrix = value_matrix.get(influencer_name)
        if not matrix:
            return matrix["base"] if matrix else 1000
            
        return matrix["premium"] if content_quality == "high" else matrix["base"]
    
    @staticmethod
    def generate_custom_request(influencer_name, client_brief):
        """Handle custom high-ticket influencer requests."""
        print(f"[{datetime.now()}] Generating custom brief for {influencer_name}")
        return {"custom_request": True, "client_brief": client_brief}

# --- STEP 1: GENERATE CONTENT FROM LM STUDIO ---
def generate_creative_brief(influencer_name, config):
    print(f"[{datetime.now()}] Querying LM Studio for {influencer_name}...")
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": config["system_prompt"]},
            {"role": "user", "content": "Generate today's viral lifestyle image prompt and posting caption based on your persona."}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    response = requests.post(LM_STUDIO_URL, headers=headers, json=data)
    raw_content = response.json()['choices']['message']['content']
    return json.loads(raw_content)

# --- STEP 2: TRIGGER COMFYUI API WITH INSTANTID & FIXED SEED ---
def generate_image_via_comfy(prompt_text, influencer_name, fixed_seed):
    print(f"[{datetime.now()}] Triggering ComfyUI Workflow for {influencer_name}...")
    
    with open("flux_instantid_template.json", "r") as f:
        workflow = json.load(f)
        
    # Adjust these node IDs to match your precise JSON generation:
    # Node 6 = Positive Text Encode (CLIP) - INPUT TEXT
    workflow["6"]["inputs"]["text"] = prompt_text
    
    # Node 3 = KSampler - FIXED SEED IN PARAMS
    workflow["3"]["params"]["seed"] = fixed_seed
    
    # Node 14 = Load Image - REFERENCE ANCHOR FACE PATH
    reference_face_path = f"./agency/faces/{influencer_name}_anchor.png"
    workflow["14"]["inputs"]["path"] = reference_face_path
    
    # Establish WebSocket connection
    ws = websocket.WebSocket()
    ws.connect(f"ws://{COMFYUI_URL}/ws?clientId={uuid.uuid4()}")
    
    p = {"prompt": workflow}
    data = json.dumps(p).encode('utf-8')
    req = requests.post(f"http://{COMFYUI_URL}/prompt", data=data)
    prompt_id = req.json()['prompt_id']
    
    # Listen for completion
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                exec_data = message['data']
                if exec_data['node'] is None and exec_data['prompt_id'] == prompt_id:
                    break
                    
    # Retrieve filename from output node (node 12 = SaveImage)
    history_req = requests.get(f"http://{COMFYUI_URL}/history/{prompt_id}")
    history = history_req.json()[prompt_id]
    
    filename = history['outputs']['12']['images'][0]['filename']
    return f"C:/comfyui/output/{filename}"

# --- STEP 3: CLOUD UPLOAD HELPER FOR BUFFER ACCESS ---
def upload_to_cloud(local_path):
    print(f"[{datetime.now()}] Uploading local asset to public storage endpoint...")
    
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"File not found: {local_path}")
        
    # Use Imgur API for reliable public hosting (supports up to 4MB unauthenticated)
    return _upload_via_imgur(local_path)

def _upload_via_imgur(file_path):
    """Upload image to Imgur API for direct public access."""
    file_size = os.path.getsize(file_path)
    
    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}",
        "Content-Type": "application/octet-stream",
        "x-upload-type": "file"
    }
    
    with open(file_path, 'rb') as img_file:
        response = requests.post(IMGUR_UPLOAD_ENDPOINT, headers=headers, data=img_file)
        
    if response.status_code == 201:
        result = response.json()
        # Direct link (no Watermark) for maximum reach and quality
        direct_url = f"https://i.imgur.com/{result['data']['hash']}.png?d=direct"
        print(f"[{datetime.now()}] Imgur upload successful: {direct_url}")
        return direct_url
    else:
        raise Exception(f"Imgur upload failed: {response.status_code} - {response.text}")

# --- STEP 4: PUSH TO BUFFER FOR AUTO-SCHEDULING ---
def schedule_to_socials(caption, image_url, profile_ids):
    print(f"[{datetime.now()}] Sending content package to Buffer queue...")
    headers = {"Authorization": f"Bearer {BUFFER_ACCESS_TOKEN}"}
    
    payload = {
        "profile_ids[]": profile_ids,
        "text": caption,
        "media[photo]": image_url,
        "shorten": False,
        "now": False
    }
    
    response = requests.post(BUFFER_API_URL, headers=headers, data=payload)
    return response.json()

# --- MONETIZATION: PREMIUM CUSTOM SERVICES ---
def handle_custom_influencer_request(influencer_name, client_brief):
    """Process high-ticket custom influencer work."""
    print(f"[{datetime.now()}] Processing custom request for {influencer_name}")
    
    brief = generate_creative_brief(influencer_name, {"system_prompt": "Use the following custom instructions: " + client_brief})
    # Use default seed for custom requests (user should provide a specific influencer name)
    local_image = generate_image_via_comfy(brief["image_prompt"], influencer_name, 420691337)
    public_url = upload_to_cloud(local_image)
    
    # Custom delivery to client (not Buffer)
    print(f"[{datetime.now()}] Delivery: {public_url}")
    return {"status": "delivered", "url": public_url, "client_brief": client_brief}

import analytics_tracker
from datetime import datetime

# --- ENGINE AUTOMATION CRON ---
def run_agency_pipeline():
    print(f"\n--- STARTING DAILY AGENCY PIPELINE EXECUTION: {datetime.now()} ---")
    
    tracker = analytics_tracker.AnalyticsTracker()
    
    for name, config in INFLUENCERS.items():
        try:
            brief = generate_creative_brief(name, config)
            
            # Calculate expected value per post (for tracking ROI)
            estimated_value = MonetizationEngine.calculate_post_value(name, "high")
            print(f"[{datetime.now()}] Estimated ROI: ${estimated_value} for {name}")
            
            local_image = generate_image_via_comfy(brief["image_prompt"], name, config["fixed_seed"])
            public_url = upload_to_cloud(local_image)
            
            res = schedule_to_socials(brief["caption"], public_url, config["buffer_profile_ids"])
            print(f"Successfully processed post for {name}: {res}")
            
            # Log engagement metrics (simulated - real data would come from Buffer API)
            simulated_likes = 150 + int(hash(name) % 200)
            simulated_shares = 30 + int(hash(name) % 50)
            simulated_saves = 20 + int(hash(name) % 40)
            simulated_revenue = estimated_value * 0.8  # Simulated revenue
            
            tracker.log_engagement(
                character_id=config.get("fixed_seed", 0),
                caption=brief["caption"],
                image_url=public_url,
                likes=simulated_likes,
                shares=simulated_shares,
                saves=simulated_saves,
                revenue=simulated_revenue
            )
            
        except Exception as e:
            print(f"[{datetime.now()}] Execution Error for {name}: {str(e)}")

# Automate loop to execute at 9:00 AM daily
schedule.every().day.at("09:00").do(run_agency_pipeline)

if __name__ == "__main__":
    print("AI Agency Automation Stack online. Listening for schedule triggers...")
    while True:
        schedule.run_pending()
        time.sleep(1)
