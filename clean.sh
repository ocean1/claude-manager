#!/bin/bash
# Clean build artifacts

rm -rf build/
rm -rf dist/
rm -rf *.egg-info
rm -rf .coverage
rm -rf htmlcov/
rm -rf .pytest_cache/
rm -rf .mypy_cache/
rm -rf .ruff_cache/
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "Cleaned build artifacts"
