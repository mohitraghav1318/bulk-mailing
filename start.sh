#!/bin/bash
# =============================================================================
# start.sh — One-click setup and run for macOS / Linux users
# =============================================================================
# Make executable: chmod +x start.sh
# Run: ./start.sh
# =============================================================================

echo ""
echo "========================================"
echo "  Bulk Mailer - Starting..."
echo "========================================"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        echo "Make sure python3 is installed: sudo apt install python3-venv"
        exit 1
    fi
    echo "Virtual environment created."
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q
echo ""

# Start the app
echo "========================================"
echo "  App running at: http://localhost:5000"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""
python app.py
