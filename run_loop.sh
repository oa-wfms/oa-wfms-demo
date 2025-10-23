#!/bin/bash

# Script to run oa-wfms-demo.py in a loop with configurable interval
# Usage: ./run_loop.sh [interval_seconds]
# Default interval is 60 seconds if not specified

# Set default interval
DEFAULT_INTERVAL=60

# Get interval from command line argument or use default
INTERVAL=${1:-$DEFAULT_INTERVAL}

# Validate that interval is a positive number
if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]] || [ "$INTERVAL" -le 0 ]; then
    echo "Error: Interval must be a positive integer (seconds)"
    echo "Usage: $0 [interval_seconds]"
    echo "Example: $0 30  # Run every 30 seconds"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_FILE="$SCRIPT_DIR/oa-wfms-demo.py"
VENV_DIR="$SCRIPT_DIR/venv"
VENV_ACTIVATE="$VENV_DIR/bin/activate"

# Check if the Python file exists
if [ ! -f "$PYTHON_FILE" ]; then
    echo "Error: $PYTHON_FILE not found!"
    exit 1
fi

# Check if virtual environment exists and activate it
if [ -f "$VENV_ACTIVATE" ]; then
    echo "Activating Python virtual environment..."
    source "$VENV_ACTIVATE"
    echo "✓ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Error: Virtual environment not found at $VENV_DIR"
    echo ""
    echo "This script requires a Python virtual environment to run safely."
    echo "Please create and set up the virtual environment first:"
    echo ""
    echo "  cd $SCRIPT_DIR"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install --upgrade pip"
    echo "  pip install -r requirements.txt"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "Starting loop: Running $PYTHON_FILE every $INTERVAL seconds"
echo "Press Ctrl+C to stop, or script will stop automatically on error"
echo "----------------------------------------"

# Counter for iterations
ITERATION=1

# Main loop
while true; do
    echo "Iteration $ITERATION - $(date)"
    
    # Run the Python script
    python3 "$PYTHON_FILE"
    EXIT_CODE=$?
    
    # Check if the script ran successfully
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Completed successfully"
        
        echo "Waiting $INTERVAL seconds before next run..."
        echo "----------------------------------------"
        
        # Wait for the specified interval
        sleep "$INTERVAL"
        
        # Increment counter
        ((ITERATION++))
    else
        echo "✗ Script exited with code $EXIT_CODE"
        echo "❌ Loop interrupted due to error!"
        echo ""
        echo "ERROR DETAILS:"
        echo "- Iteration: $ITERATION"
        echo "- Timestamp: $(date)"
        echo "- Exit code: $EXIT_CODE"
        echo "- Python file: $PYTHON_FILE"
        echo ""
        
        # Provide error code explanations
        case $EXIT_CODE in
            1)
                echo "Exit code 1: General error - Check Python script for runtime errors"
                ;;
            2)
                echo "Exit code 2: Misuse of shell builtins or Python syntax error"
                ;;
            126)
                echo "Exit code 126: Command invoked cannot execute (permission problem)"
                ;;
            127)
                echo "Exit code 127: Command not found (Python not installed?)"
                ;;
            130)
                echo "Exit code 130: Script terminated by Ctrl+C"
                ;;
            *)
                echo "Exit code $EXIT_CODE: Check Python script output above for details"
                ;;
        esac
        
        echo ""
        echo "OPTIONS:"
        echo "- Press Enter to continue and restart the loop"
        echo "- Press Ctrl+C to exit completely"
        echo "- Check the Python script for issues before continuing"
        
        # Wait for user input
        read -p "Press Enter to continue or Ctrl+C to exit: "
        
        echo ""
        echo "🔄 Restarting loop..."
        echo "----------------------------------------"
        
        # Reset iteration counter and continue
        ((ITERATION++))
    fi
done