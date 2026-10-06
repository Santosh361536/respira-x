#!/usr/bin/env bash
set -o errexit

echo "📦 Upgrading build tools..."
pip install --upgrade pip setuptools wheel

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Build completed successfully."
