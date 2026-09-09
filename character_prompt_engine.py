"""
Enhanced LLM Prompt Engine for Character Development
Provides sophisticated prompt templates for deep character creation,
iterative refinement, and personality simulation.

Usage:
    from character_prompt_engine import CharacterPromptEngine
    
    engine = CharacterPromptEngine()
    response = engine.generate_character_profile("Aria_Vance", "Luxury Travel")
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import our modules
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
import character_creator


class PromptTemplate:
    """Sophisticated prompt templates for character development."""
    
    # Template 1: Detailed Character Profile Generation
    DETAILED_PROFILE_TEMPLATE = """You are an expert character designer specializing in creating realistic, engaging influencer personas. Create a comprehensive character profile based on the following parameters:

CHARACTER NAME: {name}
NICHE/INDUSTRY: {niche}
TARGET AUDIENCE: {target_audience}

OUTPUT FORMAT (MUST BE STRICT JSON):
{
    "character_name": "{name}",
    "age_range": "XX-XX years",
    "gender": "female/male/non-binary",
    "ethnicity/race": "",
    "body_type": "athletic/curvy/lean/average",
    "height_range": "X'Y to X'Z",
    "weight_range": "X-XX lbs",
    "hair_color": "",
    "hair_style": "",
    "eye_color": "",
    "skin_tone": "",
    "key_features": ["feature1", "feature2", ...],
    "personality_traits": ["trait1", "trait2", ...],
    "voice_characteristics": "description of voice tone, pitch, and speaking style",
    "speaking_style": "formal/casual/professional/conversational/enthusiastic",
    "content_focus_areas": ["focus area 1", "focus area 2"],
    "brand_positioning": "brief description of personal brand positioning"
}"""

    # Template 2: Voice and Communication Style
    VOICE_STYLE_TEMPLATE = """You are an expert voice coach and character psychologist. Describe the complete communication style for this influencer persona:

CHARACTER NAME: {name}
NICHE: {niche}
PERSONALITY TRAITS: {traits}

OUTPUT FORMAT (MUST BE STRICT JSON):
{
    "voice_tone": "description of overall vocal tone and personality",
    "speech_pattern": "how they speak in general",
    "vocal_characteristics": ["characteristic 1", "characteristic 2"],
    "language_level": "formal/conversational/professional/colloquial",
    "emotional_range": "describe emotional spectrum they express",
    "speaking_style": "how they deliver their message",
    "catchphrases_or_phrases": ["phrase1", "phrase2"],
    "sentiment_tendencies": "positive/negative/neutral",
    "language_variations": "any slang, regionalisms, or specialized terminology"
}"""

    # Template 3: Iterative Personality Refinement
    PERSONALITY_REFINEMENT_TEMPLATE = """You are an expert character designer. Based on the following character profile and feedback, refine and expand their personality traits.

CHARACTER NAME: {name}
NICHE: {niche}
CURRENT TRAITS: {current_traits_json}
FEEDBACK/ADDITIONS: {feedback_text}
TARGET AUDIENCE VIBE: {audience_vibe}

YOUR TASK:
1. Analyze the feedback and create expanded personality traits that align with both the niche and audience expectations
2. Add 3-5 new personality dimensions not currently present
3. Ensure all traits are consistent and coherent
4. Consider how personality manifests in content creation vs personal interactions

OUTPUT FORMAT (MUST BE STRICT JSON):
{
    "refined_traits": ["trait1", "trait2", ...],  // expanded list with 8-12 total traits
    "new_traits_added": ["trait1", "trait2"],  // only the new additions
    "removed_traits": [],  // any incompatible traits to remove
    "reasoning": "explanation of how feedback informed changes",
    "consistency_check": "yes/no with brief explanation"
}"""

    # Template 4: Content Style and Format Guidelines
    CONTENT_STYLE_TEMPLATE = """You are an expert content strategist for influencer marketing. Define the complete content style and format guidelines for this persona:

CHARACTER NAME: {name}
NICHE: {niche}
PERSONALITY TRAITS: {traits_json}
TARGET PLATFORMS: [{platforms}]

OUTPUT FORMAT (MUST BE STRICT JSON):
{
    "content_formats": [
        {"format_type": "reel/tiktok/short-video/story", "description": "", "duration_range": "30-60 seconds"},
        ...
    ],
    "visual_style": {
        "aesthetic": "minimalist/luxury/edgy/relaxed/professional",
        "color_palettes": ["palette1", "palette2"],
        "lighting_preference": "natural/bright/dramatic/staged",
        "camera_angles": ["frontal/three_quarter/profile/overhead"],
        "movement_style": "dynamic/static/calming"
    },
    "audio_style": {
        "music_type": "lo-fi/upbeat/cinematic/ambient/trending_tracks",
        "voice_tone": "energetic/calm/professional/conversational",
        "text_overlays": ["bold/dynamic/simple/subtle"]
    },
    "engagement_patterns": [
        {"type": "call_to_action", "description": ""},
        {"type": "question_prompt", "description": ""}
    ],
    "post_frequency_recommendation": "X posts per week",
    "best_times_to_post": ["day/time1", "day/time2"]
}"""

    # Template 5: Character Voice Simulation for Content Generation
    VOICE_SIMULATION_TEMPLATE = """You are {name}, a {niche} influencer with the following characteristics:
{personality_traits_json}
{voice_tone_description}
{speech_style_description}

Generate a post that demonstrates this character's voice and personality. The content should be engaging, authentic to their persona, and appropriate for their niche.

OUTPUT FORMAT (MUST BE STRICT JSON):
{
    "content": "the actual post text/caption",
    "tone_check": "how well this matches the character's voice",
    "engagement_potential": "high/medium/low with reasoning"
}"""


class CharacterPromptEngine:
    """Advanced LLM prompt engine for character development."""
    
    def __init__(self, LM_STUDIO_URL="http://192.168.10.105:1234/v1/chat/completions"):
        self.LM_STUDIO_URL = LM_STUDIO_URL
        self.templates = PromptTemplate()
        
    def _query_llm(self, prompt: str) -> Dict:
        """Query LM Studio API with a specific prompt."""
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "local-model",
            "messages": [
                {"role": "system", "content": "You are an expert character designer and content strategist."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(self.LM_STUDIO_URL, headers=headers, json=data)
        return response.json()['choices']['message']['content']
    
    def generate_character_profile(self, name: str, niche: str, target_audience: str = None) -> Dict:
        """Generate a comprehensive character profile."""
        
        if not target_audience:
            audience_map = {
                "Luxury Travel & Lifestyle": "high-net-worth individuals, affluent tourists 25-55",
                "Tech, AI & Gadgets": "tech enthusiasts, early adopters 18-40",
                "Personal Finance & Web3": "investors, crypto traders, finance professionals 22-50"
            }
            target_audience = audience_map.get(niche, "")
            
        prompt = self.templates.DETAILED_PROFILE_TEMPLATE.format(
            name=name,
            niche=niche,
            target_audience=target_audience
        )
        
        response_text = self._query_llm(prompt)
        
        try:
            profile = json.loads(response_text)
            return {
                "profile": profile,
                "character_name": name,
                "niche": niche,
                "generated_at": datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error in profile generation: {e}")
            return None
    
    def generate_voice_style(self, character_id: str) -> Dict:
        """Generate voice and communication style for a character."""
        bib = character_creator.get_character_bible(character_id)
        
        if not bib:
            raise ValueError(f"Character {character_id} not found")
            
        traits_str = json.dumps(bib.personality_traits, indent=2)
        
        prompt = self.templates.VOICE_STYLE_TEMPLATE.format(
            name=bib.name,
            niche=bib.niche,
            traits=traits_str
        )
        
        response_text = self._query_llm(prompt)
        
        try:
            voice_style = json.loads(response_text)
            return {
                "voice_style": voice_style,
                "character_id": character_id,
                "updated_at": datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error in voice style generation: {e}")
            return None
    
    def refine_personality(self, character_id: str, feedback_text: str) -> Dict:
        """Refine and expand personality traits based on user feedback."""
        bib = character_creator.get_character_bible(character_id)
        
        if not bib:
            raise ValueError(f"Character {character_id} not found")
            
        current_traits_str = json.dumps(bib.personality_traits, indent=2)
        
        prompt = self.templates.PERSONALITY_REFINEMENT_TEMPLATE.format(
            name=bib.name,
            niche=bib.niche,
            current_traits_json=current_traits_str,
            feedback_text=feedback_text,
            audience_vibe="engaging and authentic"
        )
        
        response_text = self._query_llm(prompt)
        
        try:
            refined_traits = json.loads(response_text)
            
            # Update character bible with new traits (simplified - in production this would be more robust)
            bib.personality_traits = refined_traits.get("refined_traits", bib.personality_traits)
            bib.updated_at = datetime.now().isoformat()
            bib.save()
            
            return {
                "character_id": character_id,
                "refined_traits": refined_traits.get("refined_traits"),
                "new_traits_added": refined_traits.get("new_traits_added", []),
                "updated_at": datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error in personality refinement: {e}")
            return None
    
    def generate_content_style(self, character_id: str) -> Dict:
        """Generate content style and format guidelines."""
        bib = character_creator.get_character_bible(character_id)
        
        if not bib:
            raise ValueError(f"Character {character_id} not found")
            
        traits_str = json.dumps(bib.personality_traits, indent=2)
        
        prompt = self.templates.CONTENT_STYLE_TEMPLATE.format(
            name=bib.name,
            niche=bib.niche,
            traits_json=traits_str,
            platforms=["Instagram", "TikTok"]
        )
        
        response_text = self._query_llm(prompt)
        
        try:
            content_style = json.loads(response_text)
            
            # Update character bible
            bib.content_style = content_style.get("content_formats", [])
            bib.updated_at = datetime.now().isoformat()
            bib.save()
            
            return {
                "character_id": character_id,
                "content_style": content_style,
                "updated_at": datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error in content style generation: {e}")
            return None
    
    def simulate_character_voice(self, character_id: str, topic: str = "intro") -> Dict:
        """Simulate character voice for a given topic."""
        bib = character_creator.get_character_bible(character_id)
        
        if not bib:
            raise ValueError(f"Character {character_id} not found")
            
        traits_str = json.dumps(bib.personality_traits, indent=2)
        voice_tone = bib.voice_tone or "friendly and professional"
        speech_style = bib.speaking_style or "conversational"
        
        prompt = self.templates.VOICE_SIMULATION_TEMPLATE.format(
            name=bib.name,
            niche=bib.niche,
            personality_traits_json=traits_str,
            voice_tone_description=voice_tone,
            speech_style_description=speech_style
        )
        
        response_text = self._query_llm(prompt)
        
        try:
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error in voice simulation: {e}")
            return None


def main():
    """Test the prompt engine."""
    from datetime import datetime
    
    engine = CharacterPromptEngine()
    
    # Test profile generation
    result = engine.generate_character_profile("Aria_Vance", "Luxury Travel & Lifestyle")
    
    if result:
        print(f"✓ Generated character profile for {result['character_name']}")
        print(f"  Niche: {result['niche']}")
        
        # Extract and display key traits
        profile = result["profile"]
        print(f"  Key features: {profile.get('key_features', [])}")
        print(f"  Personality traits: {profile.get('personality_traits', [])[:5]}...")
        print(f"  Voice characteristics: {profile.get('voice_characteristics', [])}")

if __name__ == "__main__":
    main()
