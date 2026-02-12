#!/bin/bash

echo "🚑 Hospital Tracker - Quick Start"
echo "================================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python detected"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "⚠️  IMPORTANT: Before starting the server"
echo "Edit app.py and add your HTTPSMS API key on line 25"
echo ""
echo "Press Enter when ready..."
read

# Start the application
echo "🚀 Starting Flask server..."
python3 app.py
