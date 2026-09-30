#!/usr/bin/env bash
# =============================================================================
# TIER-ITS: Ollama Setup for WSL2 (Mirrored Networking)
# =============================================================================
#
# WSL2 config this is designed for:
#   [wsl2]
#   memory=8GB
#   networkingMode=mirrored
#   localhostForwarding=true
#   dnsTunneling=true
#   firewall=false
#   autoProxy=false
#   dhcp=false
#
# IMPORTANT: With mirrored networking, Windows and WSL2 share the same port
# namespace. If something on Windows holds port 11434 (e.g. a leftover Ollama
# Windows service under svchost.exe), WSL2 Ollama cannot bind to it.
#
# This script binds to 127.0.0.1:11434 (NOT 0.0.0.0) to avoid cross-
# environment conflicts. If port 11434 is taken, check Windows side:
#   netstat.exe -ano | findstr.exe "11434"
#   taskkill.exe /F /PID <pid>
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }

# ── 1. Install Ollama (if not present) ─────────────────────────────────────
if ! command -v ollama &> /dev/null; then
    log "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    log "Ollama already installed: $(ollama --version 2>/dev/null || echo 'unknown')"
fi

# ── 2. Create data directory with correct permissions ──────────────────────
# The ollama user needs write access to /usr/share/ollama/.ollama
if [ ! -d /usr/share/ollama/.ollama ]; then
    log "Creating Ollama data directory..."
    sudo mkdir -p /usr/share/ollama/.ollama
    sudo chown -R ollama:ollama /usr/share/ollama
fi

# ── 3. Configure systemd service for WSL2 mirrored networking ──────────────
# Key: OLLAMA_HOST=127.0.0.1 (NOT 0.0.0.0)
# With mirrored networking, 0.0.0.0 causes "address already in use" if
# any Windows process touches port 11434. Using 127.0.0.1 avoids this.
log "Configuring Ollama systemd overrides..."

sudo mkdir -p /etc/systemd/system/ollama.service.d

sudo tee /etc/systemd/system/ollama.service.d/environment.conf > /dev/null << 'EOF'
[Service]
# Bind to loopback only (avoids WSL2 mirrored networking port conflicts)
Environment="OLLAMA_HOST=127.0.0.1:11434"

# Enable flash attention (reduces KV cache VRAM by ~30-50%)
Environment="OLLAMA_FLASH_ATTENTION=1"

# Limit to 1 loaded model (thermal protection for 6GB VRAM laptop)
Environment="OLLAMA_MAX_LOADED_MODELS=1"

# Keep model loaded for 5 minutes
Environment="OLLAMA_KEEP_ALIVE=5m"

# Single request at a time (thermal protection)
Environment="OLLAMA_NUM_PARALLEL=1"
EOF

log "Systemd override written"

# ── 4. Set env vars in .bashrc for CLI usage ───────────────────────────────
BASHRC="$HOME/.bashrc"
if ! grep -q 'TIER-ITS: Ollama' "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" << 'ENVBLOCK'

# --- TIER-ITS: Ollama WSL2 config ---
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_NUM_PARALLEL=1
ENVBLOCK
    log "Environment variables added to ~/.bashrc"
else
    warn "OLLAMA_HOST already in ~/.bashrc — skipping"
fi

# ── 5. Check for Windows ghost processes on port 11434 ─────────────────────
log "Checking for Windows processes on port 11434..."
if command -v netstat.exe &> /dev/null; then
    WINDOWS_PROCS=$(netstat.exe -ano 2>/dev/null | grep -c ":11434" || true)
    if [ "$WINDOWS_PROCS" -gt 0 ]; then
        warn "Found $WINDOWS_PROCS Windows connections on port 11434"
        warn "If Ollama fails to start, run: netstat.exe -ano | findstr.exe 11434"
        warn "Then kill the PID: taskkill.exe /F /PID <pid>"
    else
        log "No Windows processes on port 11434"
    fi
fi

# ── 6. Reload and restart ─────────────────────────────────────────────────
log "Reloading systemd and restarting Ollama..."
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl restart ollama

sleep 3

# ── 7. Verify the service ─────────────────────────────────────────────────
if systemctl is-active --quiet ollama; then
    log "Ollama service is running"
else
    err "Ollama service failed to start!"
    err "Check: sudo journalctl -u ollama --no-pager -n 20"
    exit 1
fi

# ── 8. Verify connectivity ────────────────────────────────────────────────
log "Testing API connectivity..."
RESPONSE=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" http://127.0.0.1:11434/ 2>/dev/null || echo "000")
if [ "$RESPONSE" = "200" ]; then
    log "API responding at http://127.0.0.1:11434/ ✓"
else
    err "API not responding (HTTP $RESPONSE)"
    err "Check: sudo journalctl -u ollama --no-pager -n 20"
    exit 1
fi

# ── 9. Verify GPU access ──────────────────────────────────────────────────
log "Checking GPU..."
if nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null; then
    log "GPU visible to system"
else
    warn "nvidia-smi failed — GPU may not be available"
fi

# ── 10. Pull project models ───────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Pulling models for TIER-ITS project"
echo "=========================================="
echo ""

log "Pulling qwen3:4b (primary extractor model, ~2.5 GB)..."
ollama pull qwen3:4b

echo ""
log "Primary model pulled."
echo ""
echo "Optional models (can be pulled later):"
echo "  ollama pull phi4-mini       # Alternative extractor (3.8B)"
echo "  ollama pull llama3.2:3b     # Fast baseline model"
echo ""

# ── 11. Final verification ────────────────────────────────────────────────
echo "=========================================="
echo " Final Verification"
echo "=========================================="
echo ""

log "Installed models:"
ollama list 2>/dev/null || warn "Could not list models"

echo ""
echo -e "${GREEN}=========================================="
echo -e " Ollama setup complete!"
echo -e "==========================================${NC}"
echo ""
echo "Usage from Python:"
echo "  from ollama import chat"
echo "  response = chat(model='qwen3:4b', messages=[...])"
echo ""
echo "Monitor GPU during inference:"
echo "  watch -n 1 nvidia-smi"
echo ""
