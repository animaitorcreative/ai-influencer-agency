"""
Character Bible Builder for AI Influencer Agency
Generates structured character profiles from conversational AI interactions.
Stores comprehensive character data with reference sheets, poses, and styling guidelines.
"""

import json
import os
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add missing imports for the character creator functions
from typing import Dict, List, Optional, Any

class CharacterBible:
    """Represents a complete character profile for the influencer agency."""
    
    def __init__(self, character_id: str):
        self.character_id = character_id
        self.name = ""
        self.niche = ""
        self.personality_traits: List[str] = []
        self.appearance = {}
        self.voice_tone = ""
        self.content_style = ""
        self.reference_images: List[Dict] = []  # URLs + descriptions
        self.pose_reference_sheets: Dict = {}
        self.lighting_setup: Dict = {}
        self.camera_directions: Dict[str, str] = {}
        self.style_preferences: Dict[str, str] = {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = None
        
    def to_dict(self) -> dict:
        """Convert character bible to serializable dictionary."""
        return {
            "character_id": self.character_id,
            "name": self.name,
            "niche": self.niche,
            "personality_traits": self.personality_traits,
            "appearance": self.appearance,
            "voice_tone": self.voice_tone,
            "content_style": self.content_style,
            "reference_images": self.reference_images,
            "pose_reference_sheets": self.pose_reference_sheets,
            "lighting_setup": self.lighting_setup,
            "camera_directions": self.camera_directions,
            "style_preferences": self.style_preferences,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def save(self, directory: str = "./agency/character_bibles"):
        """Save character bible to JSON file."""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.character_id}.json")
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load(cls, character_id: str, directory: str = "./agency/character_bibles"):
        """Load character bible from file."""
        filepath = os.path.join(directory, f"{character_id}.json")
        
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        bib = cls(character_id)
        bib.name = data.get("name", "")
        bib.niche = data.get("niche", "")
        bib.personality_traits = data.get("personality_traits", [])
        bib.appearance = data.get("appearance", {})
        bib.voice_tone = data.get("voice_tone", "")
        bib.content_style = data.get("content_style", "")
        bib.reference_images = data.get("reference_images", [])
        bib.pose_reference_sheets = data.get("pose_reference_sheets", {})
        bib.lighting_setup = data.get("lighting_setup", {})
        bib.camera_directions = data.get("camera_directions", {})
        bib.style_preferences = data.get("style_preferences", {})
        bib.created_at = data.get("created_at")
        bib.updated_at = data.get("updated_at")
        
        return bib


class CharacterCreator:
    """Interactive AI-powered character creator for building influencer personas."""
    
    def __init__(self, LM_STUDIO_URL="http://localhost:1234/v1/chat/completions"):
        self.LM_STUDIO_URL = LM_STUDIO_URL
        self.bible_dir = "./agency/character_bibles"
        
    def _query_llm(self, system_prompt: str, user_messages: List[Dict], 
                   temperature: float = 0.7) -> dict:
        """Query LM Studio API for character-related responses."""
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "local-model",
            "messages": [
                {"role": "system", "content": system_prompt},
                *user_messages,
                {"role": "user", "content": user_messages[-1]["content"]}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(self.LM_STUDIO_URL, headers=headers, json=data)
        return response.json()['choices']['message']['content']
    
    def create_character(self, name: str = None, niche: str = None):
        """Create a new character profile from scratch."""
        character_id = f"char_{name or 'custom'}_{int(time.time())}"
        
        # Initialize character bible
        bib = CharacterBible(character_id)
        bib.name = name or "Custom_Influencer"
        bib.niche = niche or "General"
        bib.appearance = {
            "age_range": "20-35",
            "gender": "",
            "ethnicity": "",
            "body_type": "athletic",
            "key_features": [],
            "style_preferences": {}
        }
        
        # Guided conversation to build character profile
        print(f"\n{'='*60}")
        print(f"Creating new character: {bib.name}")
        print("="*60)
        
        # Gather personality traits
        traits_response = self._query_llm(
            system_prompt="You are an expert character designer. Answer ONLY with a JSON list of 3-5 personality traits that fit this persona.",
            user_messages=[{"role": "user", "content": f"What personality traits define {bib.name} in the {bib.niche} niche?"}]
        )
        
        try:
            bib.personality_traits = json.loads(traits_response)
            print(f"✓ Personality traits set: {bib.personality_traits}")
        except json.JSONDecodeError:
            print("⚠ Could not parse personality traits, using defaults")
            
        # Gather appearance details
        appearance_response = self._query_llm(
            system_prompt="You are an expert character designer. Answer ONLY with a JSON object describing the character's physical appearance in detail.",
            user_messages=[{"role": "user", "content": f"Describe {bib.name}'s appearance in detail (age, gender, ethnicity, body type, hair, eyes, distinctive features)"}]
        )
        
        try:
            bib.appearance = json.loads(appearance_response)
            print("✓ Appearance details set")
        except json.JSONDecodeError:
            pass
            
        # Gather voice and content style
        voice_response = self._query_llm(
            system_prompt="Describe the voice and personality tone of this character.",
            user_messages=[{"role": "user", "content": f"What is the voice tone and personality expression for {bib.name}?"}]
        )
        
        bib.voice_tone = voice_response.strip() if isinstance(voice_response, str) else ""
        print(f"✓ Voice tone: {bib.voice_tone}")
        
        # Save initial character bible
        bib.save()
        print(f"\n✅ Character Bible created for {bib.name}")
        print(f"   Saved to: {self.bible_dir}/{bib.character_id}.json")
        
        return bib
    
    def add_reference_images(self, character_id: str, image_urls: List[str], descriptions: List[str] = None):
        """Add reference images to a character's bible."""
        bib = CharacterBible.load(character_id)
        if not bib:
            raise ValueError(f"Character {character_id} not found")
        
        for i, url in enumerate(image_urls):
            bib.reference_images.append({
                "url": url,
                "description": descriptions[i] if descriptions and i < len(descriptions) else f"Reference image {i+1}",
                "added_at": datetime.now().isoformat()
            })
            
        bib.updated_at = datetime.now().isoformat()
        bib.save()
        
    def generate_pose_reference_sheet(self, character_id: str, pose_type: str = "full_body") -> dict:
        """Generate a structured pose reference sheet for ComfyUI."""
        bib = CharacterBible.load(character_id)
        if not bib:
            raise ValueError(f"Character {character_id} not found")
        
        # Query LLM for pose directions
        system_prompt = f"You are a professional character artist and director. Generate a detailed pose reference sheet for {bib.name} in the format specified."
        
        prompt_map = {
            "full_body": "Show full body with arms and legs, natural pose",
            "frontal": "Front facing, neutral expression, both hands relaxed",
            "profile_left": "Left profile view, looking slightly toward camera",
            "profile_right": "Right profile view, looking slightly toward camera",
            "three_quarter_front": "Three-quarter front view, slight head turn to right",
            "three_quarter_back": "Three-quarter back view, slight head turn to left",
            "action_sit": "Sitting pose, relaxed posture, hands on knees or crossed",
            "action_walk": "Walking forward, natural stride, arms swinging naturally",
            "action_reach_up": "Reaching upward with one hand, other hand at side"
        }
        
        prompt = prompt_map.get(pose_type, "full body pose")
        response = self._query_llm(system_prompt, [{"role": "user", "content": f"{prompt} for {bib.name}"}, 
                                                    {"role": "user", "content": "Return ONLY a JSON object with these keys: 'camera_angle', 'body_position', 'hand_position', 'foot_position', 'head_position'"}])
        
        try:
            pose_sheet = json.loads(response)
            bib.pose_reference_sheets[pose_type] = pose_sheet
            bib.updated_at = datetime.now().isoformat()
            bib.save()
            
            print(f"✓ Pose reference sheet generated for {pose_type}")
            return pose_sheet
            
        except json.JSONDecodeError:
            print("⚠ Could not parse pose response, generating from LLM text")
            return {"pose_type": pose_type, "description": response.strip()}
    
    def generate_lighting_setup(self, character_id: str) -> dict:
        """Generate a lighting setup reference for consistent ComfyUI renders."""
        bib = CharacterBible.load(character_id)
        if not bib:
            raise ValueError(f"Character {character_id} not found")
        
        system_prompt = f"You are an expert lighting director. Create a detailed lighting setup description."
        
        response = self._query_llm(system_prompt, [
            {"role": "user", "content": f"What lighting setup would work best for {bib.name}'s aesthetic?"},
            {"role": "user", "content": "Return ONLY a JSON object with these keys: 'lighting_type', 'light_source_direction', 'key_light_intensity', 'fill_light_intensity', 'rim_light', 'background_light', 'color_temperature'}"}
        ])
        
        try:
            lighting_setup = json.loads(response)
            bib.lighting_setup = lighting_setup
            bib.updated_at = datetime.now().isoformat()
            bib.save()
            
            print(f"✓ Lighting setup generated")
            return lighting_setup
            
        except json.JSONDecodeError:
            return {"description": response.strip()}
    
    def get_character_bible(self, character_id: str) -> CharacterBible | None:
        """Retrieve a complete character bible."""
        return CharacterBible.load(character_id)
    
    def list_characters(self) -> List[str]:
        """List all available characters."""
        bib_dir = self.bible_dir
        
        if not os.path.exists(bib_dir):
            return []
            
        return [f for f in os.listdir(bib_dir) if f.endswith(".json")]

# Global instance
character_creator = CharacterCreator()
