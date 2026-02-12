#!/bin/bash

# Hospital Dashboard Quick Start Script

echo "========================================="
echo "Hospital Dashboard - Quick Start"
echo "========================================="
echo ""

# Check Python installation
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""

# Initialize database
echo "Initializing databases..."
python3 -c "from app import init_db; init_db()"
echo "✅ Databases initialized"
echo ""

# Display instructions
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To start the hospital dashboard:"
echo "  python3 app.py"
echo ""
echo "Then open your browser and go to:"
echo "  http://localhost:5000"
echo ""
echo "Default pages:"
echo "  Registration: http://localhost:5000/hospital/register"
echo "  Login:        http://localhost:5000/hospital/login"
echo ""
echo "API Endpoints (for client platform):"
echo "  GET  /api/hospitals  - Fetch all hospitals"
echo "  POST /api/request    - Submit client request"
echo ""
echo "========================================="
