#!/bin/bash
# ============================================================================
# AI Influencer Agency - Setup & Launch Script
# Run this to verify services and launch the anchor generation pipeline
# ============================================================================

echo "=== 🤖 AI Influencer Agency Setup ==="
echo ""

# Step 1: Verify LM Studio is running
echo "[1/3] Checking LM Studio (port 1234)..."
if curl -s http://localhost:1234/v1/info > /dev/null 2>&1; then
    echo "   ✅ LM Studio is RUNNING on port 1234"
else
    echo "   ⚠️  LM Studio not found! Starting it now..."
    echo ""
    echo "   Option A: Download and run LM Studio manually from https://lmstudio.com/"
    echo "            Then start it with: lmstudio-cli --port 1234"
    read -p "Press Enter to continue (or Ctrl+C to cancel)..." || exit 1
fi

# Step 2: Verify ComfyUI is running
echo ""
echo "[2/3] Checking ComfyUI (port 8188)..."
if curl -s http://127.0.0.1:8188/status > /dev/null 2>&1; then
    echo "   ✅ ComfyUI is RUNNING on port 8188"
else
    echo "   ⚠️  ComfyUI not found! Starting it now..."
    echo ""
    echo "   Option A: Install and run ComfyUI manually:"
    echo "     cd /home/durty/AI/tools/ComfyUI"
    echo "     venv/bin/python main.py --listen 0.0.0.0 --port 8188"
    echo ""
    echo "   Option B: Start it now with this command (it will block):"
    read -p "Press Enter to start ComfyUI in background..." || exit 1
    
    # Start ComfyUI in background
    nohup /home/durty/AI/tools/ComfyUI/venv/bin/python \
        /home/durty/AI/tools/ComfyUI/main.py \
        --listen 0.0.0.0 --port 8188 > /tmp/comfyui.log 2>&1 &
    echo "   ✅ Starting ComfyUI in background (PID: $!)"
    sleep 5
fi

# Step 3: Run the anchor generator
echo ""
echo "[3/3] Generating master anchor face images..."
cd /home/durty/Agency

if python3 generate_anchors.py; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Anchor images generated!"
    echo "=========================================="
    echo ""
    echo "Check these files:"
    ls -la ./agency/faces/*.png 2>/dev/null || echo "(No images found yet - check if LM Studio has models loaded)"
    
    # List available ComfyUI workflows/templates if any exist
    echo ""
    echo "ComfyUI Templates:"
    if [ -f "flux_instantid_template.json" ]; then
        echo "  ✅ flux_instantid_template.json (Flux.1 + InstantID template)"
    fi
    
else
    echo ""
    echo "❌ Anchor generation failed!"
fi

echo ""
echo "=========================================="
echo "📋 Next Steps:"
echo "=========================================="
echo ""
echo "1. Install dependencies (if not already done):"
echo "   pip install -r requirements.txt"
echo ""
echo "2. Launch the dashboard UI:"
echo "   streamlit run dashboard.py"
echo "      → Opens http://localhost:8501 in your browser"
echo ""
echo "3. Run the daily automation pipeline:"
echo "   python agency_orchestrator.py"
echo ""
echo "4. Create character reference images (if not done):"
echo "   - Place anchor face photos in ./agency/faces/"
echo "     e.g., aria_anchor.png, kai_anchor.png, lyra_anchor.png"
echo ""
echo "5. Configure .env file with your API tokens:"
echo "   cp .env.example .env"
echo "   Edit .env with: BUFFER_ACCESS_TOKEN=..., IMGUR_CLIENT_ID=..."
echo ""
