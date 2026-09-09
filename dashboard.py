"""
AI Influencer Agency Dashboard
Streamlit UI for managing characters, monitoring ComfyUI status, and controlling automation.

Run with: streamlit run dashboard.py
Requires: pip install streamlit requests websocket-client schedule
"""

import json
import os
import requests
import time
from datetime import datetime
from typing import Dict, List

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


# --- Helper Functions ---
def get_comfyui_status():
    """Get real-time ComfyUI status via WebSocket polling."""
    try:
        import websocket
        ws = websocket.WebSocket()
        ws.connect(f"ws://127.0.0.1:8188/ws")
        
        # Wait for initial status
        out = ws.recv()
        if isinstance(out, str):
            return json.loads(out)
            
        return {"status": "no_data"}
    except Exception as e:
        return {"error": str(e), "status": "offline"}


def generate_character_id(name: str) -> str:
    """Generate a unique character ID from name."""
    timestamp = int(time.time())
    sanitized_name = "".join(c for c in name.lower() if c.isalnum())
    return f"char_{sanitized_name}_{timestamp}"


# --- Dashboard Layout ---
def main():
    st.title("🤖 AI Influencer Agency")
    st.markdown("""
        <div style="color: #6b7280; font-size: 1rem; line-height: 1.6; margin-bottom: 1rem;">
            Monitor your three virtual influencers, create custom characters,
            and launch content directly to Buffer from one dashboard.
        </div>
    """, unsafe_allow_html=True)

    # Sidebar with navigation
    sidebar_cols = st.sidebar.columns(2)
    
    with sidebar_cols[0]:
        st.subheader("📊 Dashboard")
        
        # Real-time ComfyUI Status
        col1, col2 = st.columns(2)
        with col1:
            status = get_comfyui_status()
            if "error" in status:
                st.error(f"⚠️ {status['error']}")
            else:
                st.success("✅ ComfyUI Connected")
                
        with col2:
            last_run = datetime.now().strftime("%H:%M")
            st.metric("Last Pipeline Run", f"{last_run} UTC")

    with sidebar_cols[1]:
        st.subheader("⚡ Quick Actions")
        
        if not st.session_state.get("character_creation_active", False):
            btn = st.button("👤 Create Character", key="create_char_btn")
            
            if btn:
                start_character_creation()
                
        # Run pipeline button
        run_btn = st.button("▶️ Run Daily Pipeline", type="primary")
        
        if run_btn:
            run_pipeline()

# --- Character Creation Interface ---
def start_character_creation():
    """Initialize character creation flow."""
    st.session_state["character_creation_active"] = True
    st.session_state["conversation_history"] = []
    
    st.subheader("🎨 Create New Influencer Character")
    
    col1, col2 = st.columns(3)
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
            character_creator.create_character(name, niche)

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
            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [
                        {"role": "system", "content": "You are an expert character designer. Answer ONLY in JSON format."},
                        {"role": "user", "content": chat_input}
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                }
            )
            
            result = response.json()['choices']['message']['content']
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
    character_ids = character_creator.list_characters()
    
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
    bib = character_creator.get_character_bible(character_id)
    
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
