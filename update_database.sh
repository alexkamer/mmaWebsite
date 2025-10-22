#!/bin/bash
# Simple wrapper to run the database update script

echo "Starting MMA Database Update..."
echo "This may take several minutes depending on the amount of new data."
echo ""

uv run python scripts/update_data.py

echo ""
echo "Update complete! Check the output above for any errors."
