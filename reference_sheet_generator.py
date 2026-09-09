"""
Reference Sheet Generator for Character Bibles
Generates structured visual references from character bible data.
Creates pose cards, lighting setups, and camera direction guides.

Usage:
    from reference_sheet_generator import ReferenceSheetGenerator
    
    generator = ReferenceSheetGenerator()
    sheet = generator.create_reference_sheet(character_id)
    # sheet contains all visual references needed for ComfyUI workflows
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import our modules
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
import character_creator


class PoseTemplate:
    """Represents a structured pose template for ComfyUI workflows."""
    
    POSE_TYPES = {
        "full_body_front": {
            "name": "Full Body Front",
            "description": "Standing facing camera, shoulders back, arms relaxed at sides",
            "camera_angle": "Frontal",
            "head_position": "Looking straight ahead (0°)",
            "neck_position": "Neutral",
            "shoulder_position": "Shoulders level with hips, slightly rolled back",
            "arm_position": "Arms hanging naturally at sides, hands relaxed",
            "hand_position": "Palms facing forward, fingers relaxed",
            "hip_position": "Hips level with shoulders",
            "knee_position": "Knees straight",
            "foot_position": "Feet shoulder-width apart, weight evenly distributed"
        },
        "three_quarter_front": {
            "name": "Three Quarter Front",
            "description": "Slight head turn to right side, shoulders facing camera",
            "camera_angle": "Three-quarter front",
            "head_position": "Head turned 30° to the right",
            "neck_position": "Neck bent slightly with head turn",
            "shoulder_position": "Front shoulder raised slightly higher",
            "arm_position": "Front arm slightly forward, back arm more visible",
            "hand_position": "Front hand relaxed at side, back hand in pocket or by side",
            "hip_position": "Slight hip rotation matching head turn",
            "knee_position": "Knees straight with slight weight shift to front foot"
        },
        "profile_left": {
            "name": "Left Profile",
            "description": "Facing left, full profile view of face and body",
            "camera_angle": "Profile (Left)",
            "head_position": "Looking toward camera at 45° angle",
            "neck_position": "Neck slightly turned to maintain eye contact",
            "shoulder_position": "Shoulders level with hips, natural posture",
            "arm_position": "Front arm slightly forward, visible hand in frame",
            "hand_position": "Hand relaxed, fingers slightly curled",
            "hip_position": "Hip on left side facing camera",
            "knee_position": "Knees straight, weight slightly on front leg"
        },
        "three_quarter_back": {
            "name": "Three Quarter Back",
            "description": "Facing away from camera, slight head turn to show profile",
            "camera_angle": "Three-quarter back view",
            "head_position": "Head turned 30° toward camera (showing right profile)",
            "neck_position": "Neck angled to maintain eye contact with viewer",
            "shoulder_position": "Back shoulder more visible, front shoulder slightly forward",
            "arm_position": "Both arms visible from back, natural positioning",
            "hand_position": "Hands resting on hips or by sides",
            "hip_position": "Hips rotated away from camera",
            "knee_position": "Knees straight with weight on back foot"
        },
        "action_sit_relaxed": {
            "name": "Sit - Relaxed",
            "description": "Sitting in a relaxed chair or stool, leaning forward slightly",
            "camera_angle": "Three-quarter front from below eye level",
            "head_position": "Looking toward camera at slight downward angle",
            "neck_position": "Neck angled slightly with head tilt",
            "shoulder_position": "Shoulders relaxed, one slightly elevated",
            "arm_position": "Arms resting on thighs or chair arms, relaxed",
            "hand_position": "Hands open and visible, fingers relaxed",
            "hip_position": "Hips angled toward camera",
            "knee_position": "Knees bent at natural angle, feet flat on floor"
        },
        "action_sit_confident": {
            "name": "Sit - Confident",
            "description": "Sitting with posture of confidence, chin slightly up, eyes direct",
            "camera_angle": "Frontal from chest level",
            "head_position": "Looking directly at camera, chin elevated 5°",
            "neck_position": "Neck straight but head slightly forward",
            "shoulder_position": "Shoulders squared, chest open and proud",
            "arm_position": "Arms resting on desk or arms of chair, elbows bent",
            "hand_position": "Hands folded or one hand lightly touching chin",
            "hip_position": "Hips level with shoulders",
            "knee_position": "Knees bent at natural angle"
        },
        "action_walk_forward": {
            "name": "Walk Forward",
            "description": "Mid-stride walking forward, arms swinging naturally",
            "camera_angle": "Frontal from waist level",
            "head_position": "Looking slightly ahead (20°), not directly at camera",
            "neck_position": "Neck neutral with slight forward lean",
            "shoulder_position": "Shoulders level with hips, slight forward tilt",
            "arm_position": "Arms swinging in opposite phases to body movement",
            "hand_position": "Hands relaxed, fingers slightly curled",
            "hip_position": "Hips level with shoulders but slightly forward in stride",
            "knee_position": "Front knee bent at 90°, back knee straight"
        },
        "action_sit_laptop": {
            "name": "Sit with Laptop",
            "description": "Working at a desk, laptop open on lap or desk",
            "camera_angle": "Three-quarter front from eye level",
            "head_position": "Looking down at screen with slight downward gaze",
            "neck_position": "Neck bent forward slightly",
            "shoulder_position": "Shoulders relaxed but slightly elevated from laptop",
            "arm_position": "Arms supporting laptop or typing on keyboard",
            "hand_position": "Hands on keyboard or resting on edges of laptop",
            "hip_position": "Hips angled toward desk",
            "knee_position": "Knees bent to support sitting position"
        },
        "action_sit_desk": {
            "name": "Sit at Desk",
            "description": "Seated at a desk with arms resting on surface, engaged posture",
            "camera_angle": "Frontal from slightly below eye level",
            "head_position": "Looking toward camera or slightly to side",
            "neck_position": "Neck neutral with slight forward lean toward desk",
            "shoulder_position": "Shoulders relaxed, elbows bent at 90° on desk",
            "arm_position": "Arms resting on desk surface",
            "hand_position": "Hands folded or one hand lightly touching other",
            "hip_position": "Hips angled toward desk, weight slightly forward",
            "knee_position": "Knees bent at natural angle"
        },
        "action_sit_cross_legged": {
            "name": "Sit Cross-Legged",
            "description": "Sitting cross-legged in a relaxed, casual pose",
            "camera_angle": "Three-quarter front from eye level",
            "head_position": "Looking toward camera with slight tilt",
            "neck_position": "Neck slightly tilted with head movement",
            "shoulder_position": "Shoulders relaxed and natural",
            "arm_position": "Arms resting on crossed legs or beside body",
            "hand_position": "Hands resting on thighs, fingers relaxed",
            "hip_position": "Hips angled to accommodate cross-legged position",
            "knee_position": "Knees bent at 90° with one knee on top of other"
        },
        "action_sit_leaning": {
            "name": "Sit Leaning Forward",
            "description": "Sitting leaning forward over desk, engaged and interactive",
            "camera_angle": "Frontal from slightly above eye level",
            "head_position": "Looking directly at camera with direct eye contact",
            "neck_position": "Neck straight but head tilted slightly forward",
            "shoulder_position": "Shoulders forward over desk, chest elevated",
            "arm_position": "Arms resting on desk surface, elbows at 90°",
            "hand_position": "Hands folded in lap or one hand lightly touching other",
            "hip_position": "Hips angled toward camera with weight shifted forward",
            "knee_position": "Knees bent at natural angle, feet supporting posture"
        }
    }

    def __init__(self):
        self.poses = self.POSE_TYPES


class ReferenceSheetGenerator:
    """Generates comprehensive reference sheets from character bibles."""
    
    def __init__(self):
        self.pose_template = PoseTemplate()
        self.reference_dir = "./agency/reference_sheets"
        os.makedirs(self.reference_dir, exist_ok=True)
        
    def create_reference_sheet(self, character_id: str) -> Dict:
        """Create a complete reference sheet for a character."""
        bib = character_creator.get_character_bible(character_id)
        
        if not bib:
            raise ValueError(f"Character {character_id} not found")
            
        # Build the reference sheet
        ref_sheet = {
            "character_id": character_id,
            "character_name": bib.name,
            "niche": bib.niche,
            "created_at": datetime.now().isoformat(),
            "updated_at": bib.updated_at,
            "personality_traits": bib.personality_traits,
            "voice_tone": bib.voice_tone,
            "content_style": bib.content_style,
            "appearance": bib.appearance.copy() if bib.appearance else {},
            "pose_reference_sheets": {},
            "lighting_setup": {}
        }
        
        # Add pose references from character bible
        ref_sheet["poses"] = {
            key: self.pose_template.POSE_TYPES[pose_key] 
            for key, pose_data in bib.pose_reference_sheets.items()
            if key in self.pose_template.POSE_TYPES.keys()
        }
        
        # Store lighting setup if available
        if bib.lighting_setup:
            ref_sheet["lighting"] = bib.lighting_setup.copy()
            
        # Generate default poses if none exist
        if not bib.pose_reference_sheets:
            print(f"  ℹ️ No pose references found for {bib.name}. Generating defaults...")
            ref_sheet["poses"] = {
                key: self.pose_template.POSE_TYPES[key] 
                for key in ["full_body_front", "three_quarter_front", "profile_left"]
            }
            
        return ref_sheet
    
    def save_reference_sheet(self, character_id: str, reference_sheet: Dict):
        """Save reference sheet to file."""
        filename = f"{character_id}_reference.json"
        filepath = os.path.join(self.reference_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(reference_sheet, f, indent=2)
            
        print(f"✓ Reference sheet saved: {filepath}")
        return filepath
    
    def load_reference_sheet(self, character_id: str):
        """Load a reference sheet from file."""
        filename = f"{character_id}_reference.json"
        filepath = os.path.join(self.reference_dir, filename)
        
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, 'r') as f:
            return json.load(f)


class ComfyUIIntegration:
    """Integrates reference sheets with ComfyUI workflows."""
    
    def __init__(self, comfyui_url: str = "127.0.0.1:8188"):
        self.comfyui_url = comfyui_url
        
    def generate_comfyui_prompt(self, character_name: str, pose_type: str) -> Dict:
        """Generate a ComfyUI prompt based on character reference sheet."""
        
        # Get the reference sheet
        ref_sheet = ReferenceSheetGenerator().load_reference_sheet(character_name)
        
        if not ref_sheet:
            raise ValueError(f"Reference sheet not found for {character_name}")
            
        # Build the image prompt from pose data
        pose_data = ref_sheet.get("poses", {}).get(pose_type, self.pose_template.POSE_TYPES["full_body_front"])
        
        # Combine with character appearance
        appearance = ref_sheet.get("appearance", {})
        
        prompt_parts = [
            f"{character_name} {pose_data['description']}",
            f"camera angle: {pose_data['camera_angle']}",
            f"head position: {pose_data['head_position']}",
            f"arm position: {pose_data['arm_position']}"
        ]
        
        # Add appearance details if available
        if appearance.get("key_features"):
            prompt_parts.append(f"features: {', '.join(appearance['key_features'])}")
            
        return {
            "text": " ".join(prompt_parts),
            "pose_type": pose_type,
            "reference_sheet_id": character_name
        }


def main():
    """Test the reference sheet generator."""
    from datetime import datetime
    
    # Test with a sample character
    character_id = "test_character_123456"
    
    # Create a mock character bible for testing
    bib = {
        "character_id": character_id,
        "name": "Test_Influencer",
        "niche": "Test_Niche",
        "personality_traits": ["friendly", "professional"],
        "appearance": {"age_range": "20-35"},
        "pose_reference_sheets": {},
        "updated_at": datetime.now().isoformat()
    }
    
    # Test reference sheet creation
    generator = ReferenceSheetGenerator()
    ref_sheet = generator.create_reference_sheet(character_id)
    
    print(f"✓ Created reference sheet for {bib['name']}")
    print(f"  Character ID: {character_id}")
    print(f"  Niche: {bib['niche']}")
    print(f"  Personality traits: {bib['personality_traits']}")
    print(f"  Poses included: {list(ref_sheet.get('poses', {}).keys())}")

if __name__ == "__main__":
    main()
