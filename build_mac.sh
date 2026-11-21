#!/bin/bash
# Run from the project folder on a Mac:  bash build_mac.sh
set -e
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -r requirements-build.txt
pyinstaller --noconfirm --clean --windowed --name DataSorter main.py
echo
echo "Done. Your app is: dist/DataSorter.app"
