#!/bin/bash

# Get the absolute path of the directory where this script is located
PROJECT_ROOT="/home/john/Projects/Personal/john_draw"

# Navigate to the project directory
cd "$PROJECT_ROOT" || exit 1

# Ensure dependencies are up-to-date and run the app using uv
# 'uv run' will automatically create/update the .venv if needed
uv run python john_draw.py "$@"
