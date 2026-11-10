#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Syncing parking density baseline dataset..."
python seed_density_data.py || true

echo "==> Build completed successfully!"
