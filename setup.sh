#!/bin/bash

set -e

echo "======================================"
echo " Audio Forwarder Bot Setup"
echo "======================================"

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "[+] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[+] Activating virtual environment..."
source venv/bin/activate

echo "[+] Upgrading pip..."
python3 -m pip install --upgrade pip

echo "[+] Installing Python requirements..."
pip install -r requirements.txt

echo
echo "======================================"
echo " Setup Completed Successfully!"
echo "======================================"
echo
echo "Run the bot with:"
echo
echo "source venv/bin/activate"
echo "python3 main.py"