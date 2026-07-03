#!/usr/bin/env bash

set -e

echo "======================================"
echo "   Audio Forwarder Bot Setup"
echo "======================================"

echo "[1/5] Upgrading pip..."
python3 -m pip install --upgrade pip

echo "[2/5] Removing conflicting PyTgCalls packages..."
python3 -m pip uninstall -y pytgcalls py-tgcalls tgcalls ntgcalls || true

echo "[3/5] Clearing pip cache..."
python3 -m pip cache purge || true

echo "[4/5] Installing requirements..."
python3 -m pip install --no-cache-dir -r requirements.txt

echo "[5/5] Verifying installation..."

python3 - <<'EOF'
from pyrogram import Client
from pytgcalls import PyTgCalls
import ntgcalls
import numpy
import scipy
import av

print("======================================")
print("✅ Pyrogram :", Client.__module__)
print("✅ PyTgCalls: OK")
print("✅ NTgCalls :", ntgcalls.__version__)
print("✅ NumPy    :", numpy.__version__)
print("✅ SciPy    :", scipy.__version__)
print("✅ AV       :", av.__version__)
print("======================================")
EOF

echo
echo "✅ Setup Complete!"
echo
echo "Run:"
echo "python3 main.py"