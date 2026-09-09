"""
Auto-LoRa Training Pipeline for Character Consistency

Automatically prepares character data for LoRa training and sets up ComfyUI workflows.
Generates:
1. Training dataset JSON (for ComfyUI's LoraTrain)
2. ComfyUI workflow with built-in LoRA integration
3. Face landmark extraction pipeline

Usage:
    python lora_training_pipeline.py --character <name> [--images dir] [--output-dir ./lora_datasets]
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# Import our modules
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
import character_creator


@dataclass
class TrainingImage:
    """Represents a single image in the training dataset."""
    path: str  # Relative path to image file
    prompt: str
    weight: float = 1.0  # Per-image weight (0-5, default 1)
    tags: List[str] = field(default_factory=list)


class LoraDatasetBuilder:
    """Builds training datasets for ComfyUI's LoraTrain."""
    
    def __init__(self):
        self.images: List[TrainingImage] = []
        
    def add_image(self, path: str, prompt: str, weight: float = 1.0, tags: List[str] = None):
        """Add a training image with its description and metadata."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Image not found: {path}")
            
        self.images.append(TrainingImage(
            path=path,
            prompt=prompt,
            weight=weight,
            tags=tags or []
        ))
        
    def build_dataset_json(self) -> Dict:
        """Build the ComfyUI LoraTrain dataset JSON format."""
        if not self.images:
            raise ValueError("No images in training set")
            
        return {
            "files": [
                {
                    "path": img.path,
                    "prompt": img.prompt,
                    "weight": img.weight,
                    "tags": img.tags
                }
                for img in self.images
            ]
        }
        
    def save_dataset(self, output_dir: str):
        """Save the training dataset to disk."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON metadata
        json_path = os.path.join(output_dir, "train.json")
        with open(json_path, 'w') as f:
            json.dump(self.build_dataset_json(), f, indent=2)
            
        print(f"✓ Dataset saved to {json_path}")
        return json_path
        
    def get_image_count(self) -> int:
        """Return number of training images."""
        return len(self.images)


class LoraWorkflowGenerator:
    """Generates ComfyUI workflow JSON with built-in LoRa integration."""
    
    NODE_CONFIGS = {
        "CheckpointLoader": {
            "type": "CheckpointLoader",
            "inputs": [],
            "outputs": ["img"],
            "params": {
                "checkpoint_path": "/models/flux-1.5-002-base.pt",
                "use_ema": True,
                "load_infer": False
            }
        },
        "InstantID": {
            "type": "InstantID",
            "inputs": ["img"],
            "outputs": ["img"],
            "params": {
                "instantid_path": "/models/InstantID_v0.5.pt",
                "use_ema": True,
                "anchor_id": 9
            }
        },
        "PositiveTextEncode": {
            "type": "PositiveTextEncode",
            "inputs": ["text"],
            "outputs": ["positive_prompt"],
            "params": {
                "checkpoint_path": "/models/flux-1.5-002-base.pt",
                "use_ema": True,
                "dpm_solver": "euler"
            }
        },
        "NegativeTextEncode": {
            "type": "NegativeTextEncode",
            "inputs": ["text"],
            "outputs": ["negative_prompt"],
            "params": {
                "checkpoint_path": "/models/flux-1.5-002-base.pt",
                "use_ema": True,
                "dpm_solver": "euler"
            }
        },
        "KSampler": {
            "type": "KSampler",
            "inputs": ["img"],
            "outputs": ["img"],
            "params": {
                "num_steps": 25,
                "step_size": 0.1,
                "eta": 0.7,
                "eta_min": 0.0,
                "seed": 420691337,
                "noise_schedule_type": "cosine",
                "use_ema": True,
                "dpm_solver": "euler"
            }
        },
        "CFGScale": {
            "type": "CFGScale",
            "inputs": ["img"],
            "outputs": ["img"],
            "params": {
                "scale": 7.5,
                "use_ema": True,
                "dpm_solver": "euler"
            }
        },
        "LoraLoader": {
            "type": "LoRaLoader",
            "inputs": [],
            "outputs": ["lora_params"],
            "params": {
                "lora_path": "/models/lora_weights.pt",
                "use_ema": True,
                "dpm_solver": "euler"
            }
        },
        "LoraInject": {
            "type": "LoRaInject",
            "inputs": ["img"],
            "outputs": ["img"],
            "params": {
                "lora_params": None,  # Will be set dynamically
                "use_ema": True,
                "dpm_solver": "euler"
            }
        },
        "ControlNetDepth": {
            "type": "ControlNetDepth",
            "inputs": ["img"],
            "outputs": [],
            "params": {
                "controlnet_path": "/models/ControlNet_depth.pt"
            }
        },
        "ControlNetBones": {
            "type": "ControlNetBones",
            "inputs": ["img"],
            "outputs": [],
            "params": {
                "controlnet_path": "/models/ControlNet_bones.pt"
            }
        },
        "SaveImage": {
            "type": "SaveImage",
            "inputs": ["img"],
            "outputs": ["path"],
            "params": {
                "filename": "output.png",
                "save_as_png": True,
                "save_dir": "",
                "quality": 95
            }
        },
        "WebhookOutput": {
            "type": "WebhookOutput",
            "inputs": ["webhook_response"],
            "outputs": [],
            "params": {}
        },
        "Text": {
            "type": "Text",
            "inputs": ["text"],
            "outputs": ["positive_prompt"],
            "params": {}
        }
    }
    
    def generate_workflow(self, character_id: str, dataset_path: str, seed: int = 420691337) -> dict:
        """Generate a complete ComfyUI workflow JSON with LoRa integration."""
        
        # Build the workflow nodes
        nodes = self._build_nodes(character_id, dataset_path, seed)
        
        # Define connections (edges)
        edges = [
            {"from": 1, "to": 2, "node_key": "img"},  # CheckpointLoader → InstantID
            {"from": 2, "to": 3, "node_key": "img"},  # InstantID → KSampler
            {"from": 3, "to": 4, "node_key": "img"},  # KSampler → CFGScale
            {"from": 5, "to": 6, "node_key": "positive_prompt"},  # Positive Text Encode (x2)
            {"from": 7, "to": 6, "node_key": "negative_prompt"},  # Negative Text Encode → Positive Text Encode
            {"from": 8, "to": 10, "node_key": ""},  # ControlNetDepth
            {"from": 9, "to": 10, "node_key": ""},  # ControlNetBones
            {"from": 12, "to": 3, "node_key": "lora_params"},  # LoRaInject → KSampler
            {"from": 14, "to": 15, "node_key": "img"},  # Load Image → ControlNetFaceAligner
            {"from": 15, "to": 16, "node_key": ""},  # ControlNetFaceAligner (placeholder)
            {"from": 17, "to": 18, "node_key": ""},  # SaveImage → WebhookOutput
        ]
        
        return {
            "version": 2,
            "nodes": nodes,
            "edges": edges,
            "variables": {"text": ""},
            "inputs": {"text": ""}
        }
    
    def _build_nodes(self, character_id: str, dataset_path: str, seed: int) -> List[Dict]:
        """Build the list of nodes for the workflow."""
        nodes = []
        
        # Node 1: CheckpointLoader
        nodes.append({
            "id": 1,
            "type": "CheckpointLoader",
            "inputs": [],
            "outputs": ["img"],
            "params": {
                "checkpoint_path": "/models/flux-1.5-002-base.pt",
                "use_ema": True,
                "load_infer": False
            }
        })
        
        # Node 2: InstantID (face consistency)
        nodes.append({
            "id": 2,
            "type": "InstantID",
            "inputs": ["img"],
            "outputs": ["img"],
            "params": {
                "instantid_path": "/models/InstantID_v0.5.pt",
                "use_ema": True,
                "anchor_id": 9
            }
        })
        
        # Node 3: KSampler (image generation)
        nodes.append({
            "id": 3,
            "type": "KSampler",
            "inputs": ["img"],
            "outputs": ["img"],
            "params": {
                "num_steps": 25,
                "step_size": 0.1,
                "eta": 0.7,
                "eta_min": 0.0,
                "seed": seed,
                "noise_schedule_type": "cosine",
                "use_ema": True,
                "dpm_solver": "euler"
            }
        })
        
        # Node 4: CFGScale (image quality)
        nodes.append({
            "id": 4,
            "type": "CFGScale",
            "inputs": ["img"],
            "outputs": ["img"],
            "params": {
                "scale": 7.5,
                "use_ema": True,
                "dpm_solver": "euler"
            }
        })
        
        # Node 5: Positive Text Encode (CLIP)
        nodes.append({
            "id": 5,
            "type": "PositiveTextEncode",
            "inputs": ["text"],
            "outputs": ["positive_prompt"],
            "params": {
                "checkpoint_path": "/models/flux-1.5-002-base.pt",
                "use_ema": True,
                "dpm_solver": "euler"
            }
        })
        
        # Node 6: Negative Text Encode (CLIP)
        nodes.append({
            "id": 6,
            "type": "NegativeTextEncode",
            "inputs": ["text"],
            "outputs": ["negative_prompt"],
            "params": {
                "checkpoint_path": "/models/flux-1.5-002-base.pt",
                "use_ema": True,
                "dpm_solver": "euler"
            }
        })
        
        # Node 7: ControlNetDepth
        nodes.append({
            "id": 7,
            "type": "ControlNetDepth",
            "inputs": ["img"],
            "outputs": [],
            "params": {
                "controlnet_path": "/models/ControlNet_depth.pt"
            }
        })
        
        # Node 8: ControlNetBones
        nodes.append({
            "id": 8,
            "type": "ControlNetBones",
            "inputs": ["img"],
            "outputs": [],
            "params": {
                "controlnet_path": "/models/ControlNet_bones.pt"
            }
        })
        
        # Node 9: ControlNetLandmark (placeholder for landmark control)
        nodes.append({
            "id": 9,
            "type": "ControlNetLandmark",
            "inputs": ["img"],
            "outputs": [],
            "params": {
                "controlnet_path": "/models/ControlNet_landmarks.pt"
            }
        })
        
        # Node 10: LoraInject (LoRa integration)
        nodes.append({
            "id": 10,
            "type": "LoraInject",
            "inputs": ["img"],
            "outputs": ["img"],
            "params": {
                "lora_params": None,  # Will be set from LoRaLoader output
                "use_ema": True,
                "dpm_solver": "euler"
            }
        })
        
        # Node 11: LoraLoader (LoRa weights loader)
        nodes.append({
            "id": 11,
            "type": "LoraLoader",
            "inputs": [],
            "outputs": ["lora_params"],
            "params": {
                "lora_path": dataset_path,
                "use_ema": True,
                "dpm_solver": "euler"
            }
        })
        
        # Node 12: SaveImage (output)
        nodes.append({
            "id": 12,
            "type": "SaveImage",
            "inputs": ["img"],
            "outputs": ["path"],
            "params": {
                "filename": "lora_output.png",
                "save_as_png": True,
                "save_dir": "",
                "quality": 95
            }
        })
        
        # Node 13: WebhookOutput (for progress tracking)
        nodes.append({
            "id": 13,
            "type": "WebhookOutput",
            "inputs": ["webhook_response"],
            "outputs": [],
            "params": {}
        })
        
        # Node 14: Load Image (reference face)
        nodes.append({
            "id": 14,
            "type": "LoadImage",
            "inputs": [],
            "outputs": ["image"],
            "params": {
                "path": f"./agency/faces/{character_id.split('_')[0]}_anchor.png"
            }
        })
        
        # Node 15: ControlNetFaceAligner (for face consistency)
        nodes.append({
            "id": 15,
            "type": "ControlNetFaceAligner",
            "inputs": ["image", "img"],
            "outputs": ["img"],
            "params": {
                "controlnet_path": "/models/InstantID_controlnet.pt"
            }
        })
        
        # Node 16: Text (positive prompt input)
        nodes.append({
            "id": 16,
            "type": "Text",
            "inputs": ["text"],
            "outputs": ["positive_prompt"],
            "params": {}
        })
        
        return nodes


class LoraTrainingManager:
    """Manages the complete LoRa training workflow."""
    
    def __init__(self, lora_model_path: str = "/models/lora_weights.pt"):
        self.lora_model_path = lora_model_path
        self.dataset_builder = LoraDatasetBuilder()
        self.workflow_generator = LoraWorkflowGenerator()
        
    def prepare_training_dataset(self, character_id: str, 
                                 image_dir: Optional[str] = None) -> Dict:
        """Prepare a training dataset from character references."""
        bib = character_creator.get_character_bible(character_id)
        
        if not bib:
            raise ValueError(f"Character {character_id} not found")
            
        # Create dataset directory
        dataset_dir = f"./agency/lora_datasets/{character_id}"
        os.makedirs(dataset_dir, exist_ok=True)
        
        print(f"\n🎨 Preparing LoRa training dataset for {bib.name}")
        print(f"   Dataset directory: {dataset_dir}")
        
        # Add reference images from character bible
        if bib.reference_images:
            for img in bib.reference_images:
                self.dataset_builder.add_image(
                    path=img["url"],
                    prompt=img.get("description", ""),
                    weight=1.0,
                    tags=["lora_train"]
                )
                
        # Add character appearance as training reference
        if bib.appearance and bib.appearance.get("key_features"):
            self.dataset_builder.add_image(
                path=f"./agency/faces/{bib.name.replace('_', '_')}_appearance.png",
                prompt="".join(bib.appearance["key_features"]),
                weight=1.5,  # Higher weight for appearance consistency
                tags=["lora_train", "character_appearance"]
            )
            
        # Create training dataset JSON
        json_path = self.dataset_builder.save_dataset(dataset_dir)
        
        print(f"✓ Dataset ready with {self.dataset_builder.get_image_count()} images")
        
        return {
            "dataset_dir": dataset_dir,
            "json_path": json_path,
            "image_count": self.dataset_builder.get_image_count()
        }
    
    def generate_training_workflow(self, character_id: str, 
                                  dataset_json_path: str,
                                  seed: int = 420691337) -> dict:
        """Generate ComfyUI workflow with LoRa integration."""
        workflow = self.workflow_generator.generate_workflow(
            character_id=character_id,
            dataset_path=dataset_json_path,
            seed=seed
        )
        
        # Save workflow JSON
        workflow_dir = f"./agency/workflows/{character_id}"
        os.makedirs(workflow_dir, exist_ok=True)
        
        with open(os.path.join(workflow_dir, "lora_training_workflow.json"), 'w') as f:
            json.dump(workflow, f, indent=2)
            
        print(f"✓ Training workflow saved to {workflow_dir}/lora_training_workflow.json")
        return workflow
    
    def generate_batch_generation_workflow(self, character_id: str, 
                                           num_images: int = 5,
                                           seeds: List[int] = None) -> dict:
        """Generate a batch image generation workflow for testing."""
        bib = character_creator.get_character_bible(character_id)
        
        if not bib:
            raise ValueError(f"Character {character_id} not found")
            
        # Create a workflow that generates multiple images with different seeds
        dataset_path = f"./agency/lora_datasets/{character_id}/train.json"
        
        workflow = self.workflow_generator.generate_workflow(
            character_id=character_id,
            dataset_path=dataset_path if os.path.exists(dataset_path) else None,
            seed=seeds[0] if seeds else 420691337
        )
        
        # Add batch generation configuration
        workflow["batch_config"] = {
            "num_images": num_images,
            "seed_range": range(seeds[0], seeds[0] + num_images) if seeds else None,
            "seeds": seeds or [420691337] * num_images
        }
        
        return workflow


def main():
    """Test the LoRa training pipeline."""
    from datetime import datetime
    
    # Initialize manager
    train_manager = LoraTrainingManager()
    
    print("🤖 AI Influencer Agency - LoRa Training Pipeline")
    print("=" * 60)
    
    # Test with each character
    for name in ["Aria_Vance", "Kai_Cypher", "Lyra_Quant"]:
        bib = character_creator.get_character_bible(name)
        
        if bib:
            print(f"\n🎭 Processing {bib.name}...")
            
            # Prepare dataset
            result = train_manager.prepare_training_dataset(bib.character_id)
            
            # Generate workflow
            workflow = train_manager.generate_training_workflow(
                bib.character_id,
                result["json_path"],
                bib.fixed_seed if hasattr(bib, 'fixed_seed') else 420691337
            )
            
            print(f"✅ Complete: Dataset ready with {result['image_count']} images")
        else:
            print(f"\n⚠️ Character {name} not found in character bibles")

if __name__ == "__main__":
    main()
