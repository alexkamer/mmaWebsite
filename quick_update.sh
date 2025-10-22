#!/bin/bash
# Quick Update - Simple wrapper for daily/weekly MMA database updates

echo "🥊 MMA Database Quick Update"
echo "=============================="
echo ""

# Check if days argument provided
DAYS=${1:-90}

echo "📅 Checking fighters active in last $DAYS days..."
echo "⏱️  Estimated time: 2-10 minutes"
echo ""

# Run the incremental update
uv run python scripts/incremental_update.py --days $DAYS

echo ""
echo "✅ Update complete!"
echo ""
echo "💡 Tips:"
echo "   - Run daily: ./quick_update.sh 30"
echo "   - Run weekly: ./quick_update.sh 90"
echo "   - Run monthly backfill: see docs/DATA_UPDATE_GUIDE.md"
