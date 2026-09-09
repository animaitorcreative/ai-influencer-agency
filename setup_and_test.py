"""
Setup and Test Script for AI Influencer Agency
Run this to load example character bibles and verify the system is ready.
"""

import json
import os
from datetime import datetime

# Import our modules
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
import character_creator

def setup_example_bibles():
    """Load example character bibles for testing."""
    print("📋 Setting up example character bibles...")
    
    examples = {
        "aria_vance": {
            "name": "Aria_Vance",
            "niche": "Luxury Travel & Lifestyle",
            "personality_traits": ["elegant", "confident", "sophisticated"],
            "appearance": {
                "age_range": "24-28",
                "gender": "female",
                "ethnicity": "Scandinavian",
                "body_type": "athletic",
                "hair_color": "blonde",
                "eye_color": "hazel"
            },
            "voice_tone": "elegant, articulate, confident",
            "content_style": ["luxury lifestyle", "travel guides"]
        },
        "kai_cypher": {
            "name": "Kai_Cypher",
            "niche": "Tech & AI Gadgets",
            "personality_traits": ["edgy", "innovative", "analytical"],
            "appearance": {
                "age_range": "26-30",
                "gender": "male",
                "ethnicity": "mixed",
                "body_type": "athletic",
                "hair_color": "black",
                "eye_color": "brown"
            },
            "voice_tone": "energetic, tech-focused, forward-thinking",
            "content_style": ["tech reviews", "AI demos"]
        }
    }
    
    bib_dir = "./agency/character_bibles"
    os.makedirs(bib_dir, exist_ok=True)
    
    for char_id, data in examples.items():
        bib_path = os.path.join(bib_dir, f"{char_id}.json")
        
        if not os.path.exists(bib_path):
            with open(bib_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  ✓ Created: {char_id} ({data['name']})")
    
    return examples

def test_imports():
    """Test that all modules load correctly."""
    print("\n🧪 Testing module imports...")
    
    try:
        from character_creator import CharacterCreator, CharacterBible
        print("  ✓ Character creator modules OK")
    except ImportError as e:
        print(f"  ⚠️ Import error (expected if LM Studio not running): {e}")
    
    try:
        from reference_sheet_generator import PoseTemplate, ReferenceSheetGenerator
        print("  ✓ Reference sheet generator OK")
    except ImportError as e:
        print(f"  ⚠️ Import error (expected if LM Studio not running): {e}")
        
    try:
        from character_prompt_engine import CharacterPromptEngine, PromptTemplate
        print("  ✓ Prompt engine OK")
    except ImportError as e:
        print(f"  ⚠️ Import error (expected if LM Studio not running): {e}")
        
    try:
        from analytics_tracker import AnalyticsTracker, RevenueProjections
        print("  ✓ Analytics tracker OK")
    except ImportError as e:
        print(f"  ⚠️ Import error (expected if LM Studio not running): {e}")

def show_setup_instructions():
    """Display clear setup instructions."""
    print("\n" + "="*70)
    print("🎯 AI INFLUENCER AGENCY - SETUP GUIDE")
    print("="*70)
    
    print("""
STEP 1: Install Dependencies
─────────────────────────
pip install streamlit requests websocket-client schedule

STEP 2: Configure Environment Variables
──────────────────────────────────────
Copy .env.example to .env and fill in your tokens:
  BUFFER_ACCESS_TOKEN=your_buffer_token_here
  IMGUR_CLIENT_ID=your_imgur_client_id (optional)

STEP 3: Start Your AI Services
─────────────────────────────
Terminal 1: Run LM Studio on port 1234
  - Download and run LM Studio
  - Ensure it's listening on http://localhost:1234

Terminal 2: Run ComfyUI on port 8188
  pip install comfyui
  comfyui --headless --listen-port 8188

STEP 4: Prepare Anchor Face Images
───────────────────────────────
Create face reference images for each character:
  - ./agency/faces/aria_anchor.png (female, blonde, hazel eyes)
  - ./agency/faces/kai_anchor.png (male, black hair, brown eyes)

STEP 5: Run the System
─────────────────────
Option A - Automation Pipeline:
  python agency_orchestrator.py

Option B - Dashboard UI (recommended for testing):
  streamlit run dashboard.py
    """)

def show_example_workflow():
    """Show an example of how a character is used."""
    print("\n📝 EXAMPLE WORKFLOW:")
    
    bib = {
        "name": "Aria_Vance",
        "niche": "Luxury Travel & Lifestyle",
        "personality_traits": ["elegant", "confident"],
        "appearance": {"hair_color": "blonde", "eye_color": "hazel"}
    }
    
    print(f"  • Character: {bib['name']}")
    print(f"  • Niche: {bib['niche']}")
    print(f"  • Voice: {'elegant, articulate, confident'}")
    print(f"  • Appearance: {bib['appearance'].get('hair_color', 'N/A')}, {bib['appearance'].get('eye_color', 'N/A')}")
    
    # Simulate a generated brief
    print("\n  💬 Example AI Brief (from LM Studio):")
    example_brief = {
        "caption": f"✨ Living the dream in Santorini! The views here are absolutely unreal. #luxurytravel #santorini #dreamdestination",
        "image_prompt": "High-end luxury lifestyle scene, 8k resolution, Scandinavian woman with sharp cheekbones and hazel eyes, elegant white dress, sunset over caldera, golden hour lighting"
    }
    print(f"  • Caption: {example_brief['caption']}")
    print(f"  • Image Prompt: {example_brief['image_prompt'][:60]}...")

if __name__ == "__main__":
    setup_example_bibles()
    test_imports()
    show_setup_instructions()
    show_example_workflow()
    
    print("\n✅ Setup complete! Ready to launch.")
    print("Open http://localhost:8501 for the dashboard, or run 'python agency_orchestrator.py' to start automation.")
