#!/usr/bin/env bash
# =====================================================================
# Audio Forwarder Bot - setup script
# Usage:  bash setup.sh
# =====================================================================
set -euo pipefail

echo "=============================================="
echo "  Audio Forwarder Bot - setup"
echo "=============================================="

# 1) System dependency: ffmpeg (required by py-tgcalls)
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[!] ffmpeg not found. Please install it:"
  echo "      Debian/Ubuntu : sudo apt update && sudo apt install -y ffmpeg"
  echo "      Fedora        : sudo dnf install -y ffmpeg"
  echo "      macOS (brew)  : brew install ffmpeg"
else
  echo "[ok] ffmpeg found: $(ffmpeg -version | head -n1)"
fi

# 2) Python virtual environment
if [ ! -d "venv" ]; then
  echo "[*] Creating virtual environment (venv)..."
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate

# 3) Python dependencies
echo "[*] Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 4) Credentials
if [ ! -f ".env" ]; then
  echo "[*] Creating .env from template (edit it with your real values)..."
  cp .env.example .env
fi

echo ""
echo "=============================================="
echo "  Setup complete"
echo "=============================================="
echo "1. Edit your credentials:   nano .env"
echo "2. Run the bot:             bash run.sh"
echo "   (or)  source venv/bin/activate && set -a && source .env && set +a && python3 main.py"
echo ""
echo "SECURITY: rotate any previously shared bot token / string session."
