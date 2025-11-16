#!/usr/bin/env python3
"""
Backfill Missing Fighter Events
Uses the per-fighter eventlog endpoint to find and add missing fights to the database.

This is much more efficient than scraping all events chronologically because:
1. The eventlog gives us a complete list of ALL fights for a fighter
2. We can target specific missing events rather than re-processing everything
3. It's fighter-centric, so we catch regional/promotional fights we might miss
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Set

from mma_website.utils.helpers import process_event
from archive.db import Card, Fight, add_to_db


def get_all_fighter_ids() -> List[int]:
    """Get all fighter IDs from the database"""
    conn = sqlite3.connect('data/mma.db')
    cursor = conn.cursor()
    fighter_ids = [row[0] for row in cursor.execute("SELECT id FROM athletes").fetchall()]
    conn.close()
    return fighter_ids


def get_existing_fight_ids() -> Set[Tuple[str, int, int]]:
    """Get all existing (league, event_id, fight_id) combinations"""
    conn = sqlite3.connect('data/mma.db')
    cursor = conn.cursor()
    fights = set(cursor.execute("SELECT league, event_id, fight_id FROM fights").fetchall())
    conn.close()
    return fights


def get_existing_event_ids() -> Set[Tuple[str, int]]:
    """Get all existing (league, event_id) combinations"""
    conn = sqlite3.connect('data/mma.db')
    cursor = conn.cursor()
    events = set(cursor.execute("SELECT league, event_id FROM cards").fetchall())
    conn.close()
    return events


def add_to_db_silent(data, model_class):
    """
    Wrapper around add_to_db that suppresses verbose duplicate messages.
    Returns (success_count, duplicate_count)
    """
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    
    # Capture stdout/stderr to suppress duplicate messages
    f = io.StringIO()
    try:
        with redirect_stdout(f), redirect_stderr(f):
            add_to_db(data, model_class)
        # Check if it was a duplicate (IntegrityError)
        output = f.getvalue()
        if 'duplicate' in output.lower() or 'integrity' in output.lower():
            return (0, 1)
        return (1, 0)
    except Exception:
        return (0, 1)


def fetch_fighter_eventlog(fighter_id: int, limit: int = 300) -> List[Dict]:
    """
    Fetch a fighter's complete eventlog

    Returns:
        List of event dictionaries with event_id, competition_id, and league
    """
    url = f"https://sports.core.api.espn.com/v2/sports/mma/athletes/{fighter_id}/eventlog?lang=en&region=us&limit={limit}"

    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        events = []
        for item in data.get('events', {}).get('items', []):
            # Extract event info
            event_ref = item.get('event', {}).get('$ref', '')
            comp_ref = item.get('competition', {}).get('$ref', '')

            if not event_ref or not comp_ref:
                continue

            # Parse league, event_id, and competition_id from URLs
            # Format: .../leagues/{league}/events/{event_id}/competitions/{comp_id}...
            try:
                league = comp_ref.split('leagues/')[1].split('/')[0]
                event_id = int(comp_ref.split('events/')[1].split('/')[0])
                comp_id_str = comp_ref.split('competitions/')[1].split('?')[0]
                comp_id = int(comp_id_str)  # Convert to int to match database

                events.append({
                    'league': league,
                    'event_id': event_id,
                    'comp_id': comp_id,
                    'event_url': event_ref.split('?')[0],
                    'comp_url': comp_ref.split('?')[0]
                })
            except (IndexError, ValueError) as e:
                print(f"  ⚠️  Failed to parse refs for fighter {fighter_id}: {e}")
                continue

        return events

    except Exception as e:
        print(f"  ❌ Error fetching eventlog for fighter {fighter_id}: {e}")
        return []


def find_missing_data(fighter_id: int, existing_fights: Set, existing_events: Set) -> Tuple[List, List]:
    """
    Find missing fights and events for a fighter

    Returns:
        (missing_fights, missing_events) - Lists of fight and event info
    """
    eventlog = fetch_fighter_eventlog(fighter_id)

    missing_fights = []
    missing_events_dict = {}  # Use dict to deduplicate by (league, event_id)

    for event in eventlog:
        league = event['league']
        event_id = event['event_id']
        comp_id = event['comp_id']

        # Check if fight is missing
        if (league, event_id, comp_id) not in existing_fights:
            missing_fights.append(event)
            
            # If fight is missing, we need to backfill the entire event
            # This ensures we get all fights from that event, not just this one
            event_key = (league, event_id)
            if event_key not in missing_events_dict:
                missing_events_dict[event_key] = event

    missing_events = list(missing_events_dict.values())
    return missing_fights, missing_events


def backfill_missing_events(missing_events: List[Dict], max_workers: int = 10):
    """Backfill missing events (cards)"""
    if not missing_events:
        return

    print(f"\n📥 Backfilling {len(missing_events)} missing events...")

    # Deduplicate by (league, event_id)
    unique_events = {}
    for event in missing_events:
        key = (event['league'], event['event_id'])
        if key not in unique_events:
            unique_events[key] = event

    added_cards = 0
    added_fights = 0
    skipped_cards = 0
    skipped_fights = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        event_urls = [f"{event['event_url']}?lang=en&region=us" for event in unique_events.values()]
        futures = {executor.submit(process_event, url): url for url in event_urls}

        for future in as_completed(futures):
            url = futures[future]
            try:
                card, fights = future.result()

                if card:
                    success, duplicates = add_to_db_silent(card, Card)
                    added_cards += success
                    skipped_cards += duplicates

                for fight in fights:
                    success, duplicates = add_to_db_silent(fight, Fight)
                    added_fights += success
                    skipped_fights += duplicates

            except Exception as e:
                print(f"  ⚠️  Error processing event {url}: {e}")

    print(f"  ✅ Added {added_cards} new cards and {added_fights} new fights")
    if skipped_cards > 0 or skipped_fights > 0:
        print(f"  ℹ️  Skipped {skipped_cards} duplicate cards and {skipped_fights} duplicate fights")


def backfill_sample_fighters(sample_size: int = 100):
    """
    Backfill missing data for a sample of fighters
    This is useful for testing or partial backfills
    """
    print("\n" + "🥊" * 30)
    print("FIGHTER EVENTLOG BACKFILL (SAMPLE)")
    print("🥊" * 30)

    # Get data
    print("\n📊 Loading existing data...")
    fighter_ids = get_all_fighter_ids()
    existing_fights = get_existing_fight_ids()
    existing_events = get_existing_event_ids()

    print(f"  Total fighters: {len(fighter_ids)}")
    print(f"  Existing fights: {len(existing_fights)}")
    print(f"  Existing events: {len(existing_events)}")

    # Sample fighters
    import random
    sample_fighters = random.sample(fighter_ids, min(sample_size, len(fighter_ids)))

    print(f"\n🔍 Checking {len(sample_fighters)} fighters for missing data...")

    all_missing_fights = []
    all_missing_events = []
    fighters_with_missing_data = 0

    for i, fighter_id in enumerate(sample_fighters, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(sample_fighters)} fighters checked...")

        missing_fights, missing_events = find_missing_data(fighter_id, existing_fights, existing_events)

        if missing_fights or missing_events:
            fighters_with_missing_data += 1
            all_missing_fights.extend(missing_fights)
            all_missing_events.extend(missing_events)
            print(f"  Fighter {fighter_id}: {len(missing_fights)} missing fights, {len(missing_events)} missing events")

    print(f"\n📊 Results:")
    print(f"  Fighters with missing data: {fighters_with_missing_data}/{len(sample_fighters)}")
    print(f"  Total missing fights: {len(all_missing_fights)}")
    print(f"  Total missing events: {len(all_missing_events)}")

    # Backfill
    if all_missing_events:
        backfill_missing_events(all_missing_events)
    else:
        print("\n✅ No missing data to backfill!")


def backfill_all_fighters(batch_size: int = 100):
    """
    Backfill missing data for ALL fighters
    This is a comprehensive backfill that may take several hours
    """
    print("\n" + "🥊" * 30)
    print("FIGHTER EVENTLOG BACKFILL (FULL)")
    print("🥊" * 30)
    print("\n⚠️  WARNING: This will check ALL fighters and may take several hours!")

    # Get data
    print("\n📊 Loading existing data...")
    fighter_ids = get_all_fighter_ids()
    existing_fights = get_existing_fight_ids()
    existing_events = get_existing_event_ids()

    print(f"  Total fighters: {len(fighter_ids)}")
    print(f"  Existing fights: {len(existing_fights)}")
    print(f"  Existing events: {len(existing_events)}")

    print(f"\n🔍 Checking all {len(fighter_ids)} fighters for missing data...")
    print(f"  Processing in batches of {batch_size}...")

    total_added_cards = 0
    total_added_fights = 0
    total_fighters_with_missing = 0

    # Process in batches
    num_batches = (len(fighter_ids) + batch_size - 1) // batch_size
    for batch_num in range(num_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(fighter_ids))
        batch_fighters = fighter_ids[batch_start:batch_end]

        print(f"\n📦 Batch {batch_num + 1}/{num_batches}: Fighters {batch_start+1}-{batch_end} ({len(batch_fighters)} fighters)")

        batch_missing_fights = []
        batch_missing_events = []
        batch_fighters_with_missing = 0

        for i, fighter_id in enumerate(batch_fighters):
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{len(batch_fighters)} fighters in batch checked...")
            
            missing_fights, missing_events = find_missing_data(fighter_id, existing_fights, existing_events)
            if missing_fights or missing_events:
                batch_fighters_with_missing += 1
                batch_missing_fights.extend(missing_fights)
                batch_missing_events.extend(missing_events)

        print(f"  📊 Batch results:")
        print(f"     Fighters with missing data: {batch_fighters_with_missing}/{len(batch_fighters)}")
        print(f"     Missing fights found: {len(batch_missing_fights)}")
        print(f"     Missing events found: {len(batch_missing_events)}")

        total_fighters_with_missing += batch_fighters_with_missing

        if batch_missing_events:
            backfill_missing_events(batch_missing_events)
            # Update existing sets with new data
            existing_fights = get_existing_fight_ids()
            existing_events = get_existing_event_ids()
        else:
            print("  ✅ No missing data in this batch!")

    print("\n" + "="*60)
    print("✅ FULL BACKFILL COMPLETE!")
    print("="*60)
    print(f"  Total fighters with missing data: {total_fighters_with_missing}/{len(fighter_ids)}")
    print(f"  Final database state:")
    print(f"    Total fights: {len(existing_fights)}")
    print(f"    Total events: {len(existing_events)}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill missing fighter events using eventlog endpoint')
    parser.add_argument('--mode', choices=['sample', 'full', 'fighter'], default='sample',
                       help='Backfill mode: sample (100 random fighters), full (all fighters), or fighter (specific ID)')
    parser.add_argument('--fighter-id', type=int, help='Specific fighter ID to check (use with --mode fighter)')
    parser.add_argument('--sample-size', type=int, default=100, help='Sample size for sample mode')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for full mode')

    args = parser.parse_args()

    try:
        if args.mode == 'sample':
            backfill_sample_fighters(sample_size=args.sample_size)
        elif args.mode == 'full':
            backfill_all_fighters(batch_size=args.batch_size)
        elif args.mode == 'fighter':
            if not args.fighter_id:
                print("❌ Error: --fighter-id required for fighter mode")
                sys.exit(1)

            print(f"\n🔍 Checking fighter {args.fighter_id}...")
            existing_fights = get_existing_fight_ids()
            existing_events = get_existing_event_ids()

            missing_fights, missing_events = find_missing_data(args.fighter_id, existing_fights, existing_events)

            print(f"\n📊 Results:")
            print(f"  Missing fights: {len(missing_fights)}")
            print(f"  Missing events: {len(missing_events)}")

            if missing_events:
                backfill_missing_events(missing_events)
            else:
                print("\n✅ No missing data!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
