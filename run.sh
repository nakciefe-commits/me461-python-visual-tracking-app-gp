#!/bin/bash
# Starts the game. Works from any folder.
#
# Before starting, it makes sure the libraries are installed:
#   - creates the .venv folder if it does not exist yet
#   - installs requirements.txt the first time, and again whenever
#     requirements.txt changes (e.g. after a git pull that added a library)
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    echo "Creating the Python environment (.venv)..."
    if ! python3 -m venv .venv; then
        echo "Could not create .venv. On Ubuntu run:  sudo apt install -y python3-venv"
        exit 1
    fi
fi

# .venv/installed-requirements.txt is a copy of requirements.txt from the last
# successful install. If the two differ, something new needs installing.
if ! cmp -s requirements.txt .venv/installed-requirements.txt; then
    echo "Installing libraries from requirements.txt..."
    if ! .venv/bin/pip install -r requirements.txt; then
        echo "Installing the libraries failed. Check your internet connection and try again."
        exit 1
    fi
    cp requirements.txt .venv/installed-requirements.txt
fi

.venv/bin/python main.py
