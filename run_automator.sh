#!/bin/bash

# Your API Key is loaded here
export GEMINI_API_KEY="AIzaSyC0g_HtgprOcDHScFsANIGGFSlnhaaDuSQ" 

# Execute the Python script using the Python interpreter inside the virtual environment.
/home/ruraljoe/ai_venv/bin/python /home/ruraljoe/product_automator.py

# Pauses the terminal for output visibility
echo "Automation script finished. Press Enter to close."
read -r
