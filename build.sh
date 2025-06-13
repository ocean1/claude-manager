#!/bin/bash
# Build distribution packages

# Clean first
./clean.sh

# Build
python -m build

echo "Build complete"
