#!/usr/bin/env python3
"""
Create Seed Database for MMA Website
Fast setup with essential data for testing/development
- Top 100 UFC fighters (champions + contenders)
- Last 2 UFC events
- Current UFC rankings
- Takes 2-3 minutes instead of 30 minutes
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import from existing scripts
from mma_website.utils.helpers import (
    get_athlete_info,
    process_event,
    get_odds_data,
    get_stat_data
)
from utils.helpers import get_league_urls, fetch_and_map_league

# Create tables using archive db module (has table definitions)
from archive.db import (
    add_to_db, League, Athlete, Card, Fight, Odds, StatisticsForFight,
    create_tables
)

def print_progress(text):
    """Print progress message"""
    print(f"  → {text}")

def get_ufc_league():
    """Get UFC league information"""
    print_progress("Fetching UFC league info...")
    ufc_url = "http://sports.core.api.espn.com/v2/sports/mma/leagues/ufc?lang=en&region=us"
    league_mapping, _ = fetch_and_map_league(ufc_url)
    add_to_db(league_mapping, League)
    return league_mapping

def get_top_ufc_fighters(limit=100):
    """Get top UFC fighters from athlete list"""
    print_progress(f"Fetching top {limit} UFC fighters...")

    base_url = "https://sports.core.api.espn.com/v2/sports/mma/athletes"
    params = {"lang": "en", "region": "us", "limit": limit}

    response = httpx.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()

    athlete_urls = [item.get("$ref") for item in data.get("items", [])]

    print_progress(f"Processing {len(athlete_urls)} fighters...")
    athletes_added = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_athlete_info, url): url for url in athlete_urls}
        for future in as_completed(futures):
            try:
                athlete_data = future.result()
                add_to_db(athlete_data, Athlete)
                athletes_added += 1
                if athletes_added % 10 == 0:
                    print_progress(f"  Added {athletes_added}/{len(athlete_urls)} fighters...")
            except Exception as e:
                print(f"    ⚠ Error processing fighter: {e}")

    return athletes_added

def get_recent_ufc_events(count=2):
    """Get recent UFC events"""
    print_progress(f"Fetching last {count} UFC events...")

    # Get UFC events list
    events_url = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events?lang=en&region=us&limit=10"
    response = httpx.get(events_url)
    response.raise_for_status()
    events_data = response.json()

    # Get event URLs (they're in reverse chronological order)
    event_items = events_data.get("items", [])[:count]
    event_urls = [item.get("$ref") for item in event_items]

    print_progress(f"Processing {len(event_urls)} events...")
    fights_added = 0
    events_added = 0

    for event_url in event_urls:
        try:
            card, fights = process_event(event_url)
            if card:
                add_to_db(card, Card)
                events_added += 1
                print_progress(f"  Added event: {card.get('event_name', 'Unknown')}")

                for fight in fights:
                    add_to_db(fight, Fight)
                    fights_added += 1

                    # Get odds if available
                    if fight.get('odds_url'):
                        try:
                            odds_data = get_odds_data(fight['odds_url'])
                            add_to_db(odds_data, Odds)
                        except:
                            pass

                    # Get statistics if available
                    for i in [1, 2]:
                        stat_url = fight.get(f'fighter_{i}_statistics')
                        if stat_url:
                            try:
                                stat_data = get_stat_data(stat_url)
                                add_to_db(stat_data, StatisticsForFight)
                            except:
                                pass

        except Exception as e:
            print(f"    ⚠ Error processing event: {e}")

    return events_added, fights_added

def get_ufc_rankings():
    """Get current UFC rankings"""
    print_progress("Fetching UFC rankings...")

    try:
        # Import the rankings scraper
        from scripts.utilities.accurate_ufc_scraper import scrape_ufc_rankings
        from scripts.utilities.update_ufc_rankings import update_rankings_in_db

        rankings = scrape_ufc_rankings()
        if rankings:
            update_rankings_in_db(str(project_root / 'data' / 'mma.db'), rankings)
            print_progress(f"  Added rankings for {len(rankings)} divisions")
            return True
    except Exception as e:
        print(f"    ⚠ Could not fetch rankings: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🥊 MMA Website - Seed Database Creator".center(60))
    print("="*60 + "\n")

    print("This will create a seed database with:")
    print("  • Top 100 UFC fighters")
    print("  • Last 2 UFC events")
    print("  • Current UFC rankings")
    print("\nEstimated time: 2-3 minutes\n")

    # Create data directory if it doesn't exist
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)

    db_path = data_dir / 'mma.db'

    # Check if database already exists
    if db_path.exists() and db_path.stat().st_size > 1000:
        response = input("Database already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("\nCancelled.")
            return

        # Backup existing database
        backup_path = data_dir / f'mma.db.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        print_progress(f"Backing up existing database to {backup_path.name}")
        db_path.rename(backup_path)

    # Create tables
    print_progress("Creating database tables...")
    create_tables(str(db_path))

    try:
        # Step 1: Get UFC league info
        print("\n[1/4] Getting UFC league information...")
        get_ufc_league()

        # Step 2: Get top fighters
        print("\n[2/4] Getting top UFC fighters...")
        fighters_count = get_top_ufc_fighters(limit=100)
        print(f"  ✓ Added {fighters_count} fighters")

        # Step 3: Get recent events
        print("\n[3/4] Getting recent UFC events...")
        events_count, fights_count = get_recent_ufc_events(count=2)
        print(f"  ✓ Added {events_count} events with {fights_count} fights")

        # Step 4: Get rankings
        print("\n[4/4] Getting UFC rankings...")
        get_ufc_rankings()

        # Success!
        print("\n" + "="*60)
        print("✅ Seed database created successfully!".center(60))
        print("="*60)
        print(f"\nDatabase location: {db_path}")
        print(f"Database size: {db_path.stat().st_size / 1024 / 1024:.1f} MB")
        print("\nYou can now start the application:")
        print("  uv run run.py")
        print("\nTo get more data later:")
        print("  uv run python scripts/incremental_update.py --days 30")
        print("  uv run python scripts/backfill_fighter_events.py --mode full")
        print()

    except Exception as e:
        print(f"\n❌ Error creating seed database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
