"""
AI Influencer Agency Dashboard
Streamlit UI for managing characters, monitoring ComfyUI status, and controlling automation.

Run with: streamlit run dashboard.py
Requires: pip install streamlit requests websocket-client schedule
"""

import json
import os
import requests
import subprocess
import time
from datetime import datetime
from typing import Dict, List
from urllib.parse import urlparse

# Import our modules
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
import agency_orchestrator
import character_creator

# --- Page Configuration ---
try:
    import streamlit as st
except ImportError:
    print("Streamlit not available. Run: pip install streamlit")
    exit(1)

st.set_page_config(
    page_title="AI Influencer Agency",
    page_icon="🤖",
    layout="wide",
)

DEFAULT_LM_STUDIO_URL = os.getenv(
    "LM_STUDIO_URL",
    "http://169.254.65.222:1234/v1",
).rstrip("/")


# --- Helper Functions ---
def normalize_lm_studio_url(url: str) -> str:
    """Normalize a user-entered LM Studio URL to its OpenAI API base."""
    normalized = url.strip().rstrip("/")
    for suffix in ("/chat/completions", "/models"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
    if not normalized.endswith("/v1"):
        normalized = f"{normalized}/v1"
    return normalized


def configure_lm_studio(url: str) -> str:
    """Apply the dashboard's LM Studio setting to all in-process clients."""
    base_url = normalize_lm_studio_url(url)
    chat_url = f"{base_url}/chat/completions"
    character_creator.character_creator.LM_STUDIO_URL = chat_url
    agency_orchestrator.LM_STUDIO_URL = chat_url
    os.environ["LM_STUDIO_URL"] = base_url
    os.environ["LM_STUDIO_CHAT_URL"] = chat_url
    return base_url


def get_comfyui_status():
    """Return ComfyUI system information from its local HTTP API."""
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=3)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "status": "offline"}


def get_lm_studio_model(base_url: str):
    """Use the first model exposed by the configured LM Studio server."""
    try:
        response = requests.get(f"{base_url}/models", timeout=3)
        response.raise_for_status()
        models = response.json().get("data", [])
        return models[0]["id"] if models else None
    except requests.RequestException:
        return None


def start_local_service(service: str) -> tuple[bool, str]:
    """Start a local service using its configured installation."""
    try:
        if service == "comfyui":
            command = [
                "/home/durty/AI/tools/ComfyUI/venv/bin/python",
                "/home/durty/AI/tools/ComfyUI/main.py",
                "--listen",
                "0.0.0.0",
                "--port",
                "8188",
            ]
        elif service == "lmstudio":
            command = ["lmstudio"]
        else:
            raise ValueError(f"Unknown service: {service}")

        subprocess.Popen(
            command,
            cwd=os.path.dirname(__file__) if service == "lmstudio" else "/home/durty/AI/tools/ComfyUI",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True, f"Starting {service}..."
    except OSError as exc:
        return False, f"Could not start {service}: {exc}"


def render_service_controls(lm_url, lm_model, comfy_status):
    """Show status lights and local start controls for required services."""
    with st.sidebar.container(border=True):
        st.subheader("Local services")
        configured_url = st.text_input(
            "LM Studio base URL",
            value=lm_url,
            key="lm_studio_url",
            help="Use the OpenAI-compatible API base, for example http://169.254.65.222:1234/v1.",
        )
        configured_url = configure_lm_studio(configured_url)
        st.caption(f"Using {configured_url}")
        lm_col, lm_action = st.columns([2, 1])
        with lm_col:
            st.markdown(
                f"{'🟢' if lm_model else '🔴'} **LM Studio**"
            )
            st.caption(configured_url)
        with lm_action:
            host = urlparse(configured_url).hostname
            can_start = host in {"localhost", "127.0.0.1", "::1"}
            if not lm_model and can_start and st.button("Start", key="start_lmstudio"):
                ok, message = start_local_service("lmstudio")
                (st.success if ok else st.error)(message)
                st.rerun()
            elif not lm_model and not can_start:
                st.caption("Start it on the configured host.")

        comfy_online = "error" not in comfy_status
        comfy_col, comfy_action = st.columns([2, 1])
        with comfy_col:
            st.markdown(f"{'🟢' if comfy_online else '🔴'} **ComfyUI**")
            st.caption("127.0.0.1:8188")
        with comfy_action:
            if not comfy_online and st.button("Start", key="start_comfyui"):
                ok, message = start_local_service("comfyui")
                (st.success if ok else st.error)(message)
                st.rerun()


def get_saved_characters():
    """Load saved character bibles for the current local workspace."""
    character_ids = character_creator.character_creator.list_characters()
    return {
        character_id: character_creator.character_creator.get_character_bible(character_id)
        for character_id in character_ids
    }


def generate_content_brief(bible, instruction, lm_url):
    """Generate a caption and image prompt for a saved character."""
    model = get_lm_studio_model(lm_url)
    if not model:
        raise ConnectionError("LM Studio is not reachable on port 1234.")

    appearance = json.dumps(bible.appearance, default=str)
    response = requests.post(
        f"{lm_url}/chat/completions",
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"You are {bible.name}, a {bible.niche} creator. "
                        f"Appearance: {appearance}. Voice: {bible.voice_tone}. "
                        "Return only JSON with exactly two keys: caption and image_prompt."
                    ),
                },
                {"role": "user", "content": instruction},
            ],
            "temperature": 0.8,
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    brief = json.loads(content)
    if not {"caption", "image_prompt"} <= brief.keys():
        raise ValueError("LM Studio returned an incomplete content brief.")
    return brief


def render_analytics():
    """Render persisted engagement metrics and an explainable trend radar."""
    analytics_dir = os.path.join(os.path.dirname(__file__), "agency", "analytics")
    reports = []
    if os.path.isdir(analytics_dir):
        for filename in os.listdir(analytics_dir):
            if filename.endswith(".json"):
                with open(os.path.join(analytics_dir, filename), encoding="utf-8") as file:
                    data = json.load(file)
                posts = data.get("posts", [])
                reports.append({
                    "Character": data.get("character_id", filename[:-5]),
                    "Posts": len(posts),
                    "Likes": sum(post.get("likes", 0) for post in posts),
                    "Shares": sum(post.get("shares", 0) for post in posts),
                    "Saves": sum(post.get("saves", 0) for post in posts),
                })

    total_posts = sum(row["Posts"] for row in reports)
    total_engagement = sum(row["Likes"] + row["Shares"] + row["Saves"] for row in reports)
    with st.container(border=True):
        st.subheader("Performance")
        with st.container(horizontal=True):
            st.metric("Posts tracked", total_posts)
            st.metric("Total engagement", total_engagement)
            st.metric("Characters tracked", len(reports))
        if reports:
            st.dataframe(reports, hide_index=True)
        else:
            st.info("No engagement history yet. Generate and publish content to start tracking.")

    with st.container(border=True):
        st.subheader("Viral radar")
        st.caption("A planning heuristic based on your saved niches—not live social-platform data.")
        radar = [
            {"Trend": "Short-form behind-the-scenes", "Score": 88, "Best fit": "All characters"},
            {"Trend": "Personalized how-to carousel", "Score": 82, "Best fit": "Tech & AI / Finance"},
            {"Trend": "Aspirational day-in-the-life", "Score": 79, "Best fit": "Travel / Fashion"},
        ]
        st.dataframe(radar, hide_index=True)


# --- Dashboard Layout ---
def main():
    st.title("AI Influencer Agency")
    st.caption("Create characters, generate content, and monitor performance from your local workspace.")

    lm_url = st.session_state.get("lm_studio_url", DEFAULT_LM_STUDIO_URL)
    lm_url = configure_lm_studio(lm_url)
    lm_model = get_lm_studio_model(lm_url)
    if lm_model:
        os.environ["LM_STUDIO_MODEL"] = lm_model
    characters = get_saved_characters()
    comfy_status = get_comfyui_status()

    render_service_controls(lm_url, lm_model, comfy_status)

    overview_tab, create_tab, characters_tab = st.tabs(
        ["Overview", "Create content", "Characters"]
    )
    with overview_tab:
        render_analytics()
    with create_tab:
        render_content_workspace(characters, lm_url)
    with characters_tab:
        render_character_workspace()


def render_content_workspace(characters, lm_url):
    """Generate briefs for any saved character and optionally render an image."""
    st.subheader("Create content")
    if not characters:
        st.info("Create a character first from the Characters tab.")
        return

    character_id = st.selectbox(
        "Character",
        list(characters),
        format_func=lambda value: characters[value].name or value,
    )
    instruction = st.text_area(
        "Content direction",
        value="Create a high-retention post for today with a strong hook and a clear call to action.",
    )
    if st.button("Generate content brief", type="primary"):
        try:
            with st.spinner("Generating caption and image prompt..."):
                st.session_state["last_brief"] = generate_content_brief(
                    characters[character_id], instruction, lm_url
                )
            st.success("Content brief generated.")
        except Exception as exc:
            st.error(f"Content generation failed: {exc}")

    brief = st.session_state.get("last_brief")
    if brief:
        st.markdown("**Caption**")
        st.write(brief["caption"])
        st.markdown("**Image prompt**")
        st.write(brief["image_prompt"])
        st.caption("Image rendering is available once the ComfyUI workflow is configured for this installation.")


def render_character_workspace():
    """Create and inspect character bibles without hiding work behind a button rerun."""
    st.subheader("Characters")
    with st.form("new_character"):
        name = st.text_input("Character name", value="Custom Influencer")
        niche = st.selectbox(
            "Niche",
            ["Luxury Travel", "Tech & AI", "Personal Finance", "Fitness", "Fashion"],
        )
        submitted = st.form_submit_button("Create character", type="primary")
    if submitted:
        try:
            with st.spinner("Building character bible with LM Studio..."):
                bible = character_creator.character_creator.create_character(name, niche)
            st.success(f"Created {bible.name}.")
            st.rerun()
        except Exception as exc:
            st.error(f"Character creation failed: {exc}")

    characters = get_saved_characters()
    for character_id, bible in characters.items():
        with st.container(border=True):
            st.markdown(f"**{bible.name or character_id}**")
            st.caption(bible.niche)
            st.write(bible.voice_tone or "Voice tone not set.")


def run_pipeline():
    """Run the daily agency pipeline from the dashboard action."""
    with st.spinner("Running the daily pipeline..."):
        try:
            agency_orchestrator.run_agency_pipeline()
        except Exception as exc:
            st.error(f"Pipeline failed: {exc}")
            return
    st.success("Daily pipeline completed.")


# --- Character Creation Interface ---
def start_character_creation():
    """Initialize character creation flow."""
    st.session_state["character_creation_active"] = True
    st.session_state["conversation_history"] = []
    
    st.subheader("🎨 Create New Influencer Character")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Character Name", value="Custom_Influencer")
        
    with col2:
        niche = st.selectbox(
            "Niche", 
            options=["Luxury Travel", "Tech & AI", "Personal Finance", "Fitness", "Fashion"]
        )
        
    with col3:
        button = st.button("Start Building", type="primary")
        
        if button:
            try:
                bible = character_creator.character_creator.create_character(name, niche)
                st.session_state["current_character_name"] = bible.name
                st.success(f"Created character: {bible.name}")
            except Exception as exc:
                st.error(f"Character creation failed: {exc}")

def character_creation_interface():
    """Interactive interface for building a character bible."""
    st.subheader(f"📝 Character Bible Builder: {st.session_state['current_character_name']}")
    
    # Display conversation history
    st.divider()
    st.subheader("💬 Conversation History")
    
    if not st.session_state["conversation_history"]:
        st.info("No conversations yet. Type instructions below to build your character.")
    
    for i, message in enumerate(st.session_state["conversation_history"]):
        with st.container():
            if message.get("type") == "user":
                st.chat_message("user").write(message["content"])
            elif message.get("type") == "assistant":
                st.chat_message("ai").write(message["content"])
    
    # Add input field for user messages
    chat_input = st.text_area(
        "Type your character instructions...",
        placeholder="e.g., 'Give her a more elegant appearance with blonde hair'",
        key="character_chat"
    )
    
    if st.button("Add to Character Bible"):
        try:
            lm_url = configure_lm_studio(
                st.session_state.get("lm_studio_url", DEFAULT_LM_STUDIO_URL)
            )
            model = get_lm_studio_model(lm_url)
            if not model:
                raise ConnectionError(f"LM Studio is not reachable at {lm_url}.")
            response = requests.post(
                f"{lm_url}/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are an expert character designer. Answer ONLY in JSON format."},
                        {"role": "user", "content": chat_input}
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                },
                timeout=120,
            )
            response.raise_for_status()
            
            result = response.json()['choices'][0]['message']['content']
            st.session_state["conversation_history"].append({
                "type": "user",
                "content": chat_input
            })
            st.session_state["conversation_history"].append({
                "type": "assistant",
                "content": result
            })
        except Exception as e:
            st.error(f"Error querying LM Studio: {str(e)}")

# --- Character Bible Viewer & Editor ---
def character_bible_viewer():
    """View and edit existing character bibles."""
    st.subheader("📚 Character Bibles")
    
    # List all characters
    character_ids = character_creator.character_creator.list_characters()
    
    if not character_ids:
        st.warning("No character bibles created yet. Click 'Create New Influencer' to get started!")
        return
    
    col1, col2 = st.columns(2)
    
    for i, char_id in enumerate(character_ids):
        with col1:
            if st.button(f"Open {char_id.split('_')[0]}"):
                display_character_bible(char_id)


def display_character_bible(character_id: str):
    """Display a complete character bible with editing capabilities."""
    bib = character_creator.character_creator.get_character_bible(character_id)
    
    if not bib:
        st.error(f"Character {character_id} not found")
        return
    
    st.subheader(f"📋 Character Bible: {bib.name}")
    
    # Tab navigation for different sections
    tabs = st.tabs(["Overview", "Appearance", "Personality & Voice", "Reference Images"])
    
    with tabs[0]:
        # Overview tab - basic info
        st.markdown("### 🎯 Niche")
        st.write(bib.niche)
        
        st.markdown("### 📝 Content Style")
        st.write(bib.content_style if bib.content_style else "Not specified yet")
    
    with tabs[1]:
        # Appearance tab - visual details
        st.markdown("### 👤 Appearance Details")
        
        appearance = bib.appearance
        if appearance:
            for key, value in appearance.items():
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**{key.replace('_', ' ').title()}:**")
                    with col2:
                        st.write(value if isinstance(value, str) else json.dumps(value))


# --- Main Execution ---
if __name__ == "__main__":
    main()
