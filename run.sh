#!/bin/bash
# Starts the body tracker. Works from any folder.
cd "$(dirname "$0")"
.venv/bin/python tracker.py
