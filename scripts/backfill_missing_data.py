"""
Comprehensive script to backfill missing and incomplete data.

This script handles:
1. Missing events discovered via eventlog scraper
2. Missing competitions/fights
3. Incomplete fight results (NULL winners for completed fights)
4. Missing odds data
5. Missing statistics data
6. Missing linescore data

Usage:
    uv run python scripts/backfill_missing_data.py [--events] [--fights] [--odds] [--stats] [--linescores]
"""

import sqlite3
import httpx
import json
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set, Optional
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path to import mma_website
sys.path.insert(0, str(Path(__file__).parent.parent))

from mma_website.utils.helpers import process_event, get_odds_data, get_stat_data
from mma_website.models.database import Card, Fight, Odds, StatisticsForFight
from mma_website.utils.db_utils import add_to_db


class DataBackfiller:
    """Backfills missing and incomplete data in the database"""

    def __init__(self, db_path: str = "data/mma.db", max_workers: int = 50):
        self.db_path = db_path
        self.max_workers = max_workers
        self.stats = {
            'events_added': 0,
            'fights_added': 0,
            'fights_updated': 0,
            'odds_added': 0,
            'stats_added': 0,
            'linescores_added': 0,
            'errors': []
        }

    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    # ============================================================================
    # MISSING EVENTS
    # ============================================================================

    def backfill_missing_events(self, event_urls_file: str = "data/eventlog_entries.json"):
        """
        Backfill events that are missing from the database.
        Reads from the eventlog_entries.json file created by scrape_fighter_eventlogs.py
        """
        print("\n" + "=" * 80)
        print("BACKFILLING MISSING EVENTS")
        print("=" * 80)

        # Load eventlog entries
        eventlog_file = Path(event_urls_file)
        if not eventlog_file.exists():
            print(f"❌ Eventlog file not found: {eventlog_file}")
            print("   Run scrape_fighter_eventlogs.py first!")
            return

        with open(eventlog_file) as f:
            eventlog_entries = json.load(f)

        # Get existing event IDs
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT event_id FROM cards")
        existing_events = {row[0] for row in cursor.fetchall()}
        conn.close()

        # Find missing events
        all_event_urls = {}
        for entry in eventlog_entries:
            event_id = entry['event_id']
            if event_id not in existing_events:
                all_event_urls[event_id] = entry['event_url']

        missing_count = len(all_event_urls)
        print(f"📊 Found {missing_count} missing events to backfill")

        if missing_count == 0:
            print("✅ No missing events - database is up to date!")
            return

        # Process missing events
        print(f"🚀 Processing {missing_count} missing events...")

        processed = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_event, url): event_id
                for event_id, url in all_event_urls.items()
            }

            for future in as_completed(futures):
                event_id = futures[future]
                processed += 1

                if processed % 100 == 0:
                    print(f"  Progress: {processed}/{missing_count}")

                try:
                    card, fights = future.result()

                    # Add card
                    if card:
                        add_to_db(card, Card)
                        self.stats['events_added'] += 1

                    # Add fights
                    for fight in fights:
                        try:
                            add_to_db(fight, Fight)
                            self.stats['fights_added'] += 1
                        except Exception as e:
                            self.stats['errors'].append(f"Fight {fight.get('fight_id')}: {e}")

                except Exception as e:
                    self.stats['errors'].append(f"Event {event_id}: {e}")

        print(f"\n✅ Added {self.stats['events_added']} events and {self.stats['fights_added']} fights")

    # ============================================================================
    # INCOMPLETE FIGHTS
    # ============================================================================

    def update_incomplete_fights(self, days_back: int = 90):
        """
        Update fights that should have results but don't.
        Focuses on recent fights (last N days) that have NULL winner.
        """
        print("\n" + "=" * 80)
        print("UPDATING INCOMPLETE FIGHT RESULTS")
        print("=" * 80)

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Find fights with NULL winners from the last N days
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        query = """
            SELECT DISTINCT event_id
            FROM fights
            WHERE fighter_1_winner IS NULL
              AND fighter_2_winner IS NULL
              AND date(date) < date('now')
              AND date(date) > date(?)
        """
        cursor.execute(query, (cutoff_date,))
        event_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        print(f"📊 Found {len(event_ids)} events with incomplete results")

        if not event_ids:
            print("✅ No incomplete fights found!")
            return

        # Build event URLs
        # Note: We need to guess the league (most are 'ufc')
        print("🚀 Re-fetching event data to update results...")

        processed = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Try both UFC and 'other' leagues
            futures = {}
            for event_id in event_ids:
                for league in ['ufc', 'other']:
                    url = f"https://sports.core.api.espn.com/v2/sports/mma/leagues/{league}/events/{event_id}?lang=en&region=us"
                    futures[executor.submit(process_event, url)] = (event_id, league)

            for future in as_completed(futures):
                event_id, league = futures[future]
                processed += 1

                if processed % 50 == 0:
                    print(f"  Progress: {processed}/{len(futures)}")

                try:
                    card, fights = future.result()

                    if not card:
                        continue

                    # Update fights with results
                    for fight in fights:
                        # Use INSERT OR REPLACE to update
                        add_to_db(fight, Fight)
                        self.stats['fights_updated'] += 1

                except Exception as e:
                    # Silently skip 404s (wrong league guess)
                    if "404" not in str(e):
                        self.stats['errors'].append(f"Event {event_id} ({league}): {e}")

        print(f"\n✅ Updated {self.stats['fights_updated']} fight results")

    # ============================================================================
    # MISSING ODDS
    # ============================================================================

    def backfill_missing_odds(self):
        """Backfill odds data for fights that have odds_url but no odds records"""
        print("\n" + "=" * 80)
        print("BACKFILLING MISSING ODDS DATA")
        print("=" * 80)

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Find fights with odds_url but no odds data
        query = """
            SELECT DISTINCT f.odds_url, f.fight_id
            FROM fights f
            LEFT JOIN odds o ON f.fight_id = o.fight_id
            WHERE f.odds_url IS NOT NULL
              AND o.fight_id IS NULL
        """
        cursor.execute(query)
        missing_odds = cursor.fetchall()
        conn.close()

        print(f"📊 Found {len(missing_odds)} fights missing odds data")

        if not missing_odds:
            print("✅ No missing odds data!")
            return

        print(f"🚀 Fetching odds data...")

        processed = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(get_odds_data, url): (url, fight_id)
                for url, fight_id in missing_odds
            }

            for future in as_completed(futures):
                url, fight_id = futures[future]
                processed += 1

                if processed % 100 == 0:
                    print(f"  Progress: {processed}/{len(missing_odds)}")

                try:
                    odds_data = future.result()
                    if odds_data:
                        add_to_db(odds_data, Odds)
                        self.stats['odds_added'] += 1
                except Exception as e:
                    self.stats['errors'].append(f"Odds {fight_id}: {e}")

        print(f"\n✅ Added odds data for {self.stats['odds_added']} fights")

    # ============================================================================
    # MISSING STATISTICS
    # ============================================================================

    def backfill_missing_statistics(self):
        """Backfill statistics for fights that have stats URLs but no stats records"""
        print("\n" + "=" * 80)
        print("BACKFILLING MISSING STATISTICS DATA")
        print("=" * 80)

        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Find fights with stats URLs but no stats data
        query = """
            SELECT DISTINCT f.fighter_1_statistics, f.fighter_2_statistics
            FROM fights f
            WHERE (f.fighter_1_statistics IS NOT NULL OR f.fighter_2_statistics IS NOT NULL)
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # Flatten and deduplicate URLs
        stats_urls = set()
        for f1_url, f2_url in results:
            if f1_url:
                stats_urls.add(f1_url)
            if f2_url:
                stats_urls.add(f2_url)

        # Check which ones are missing from statistics_for_fights table
        cursor.execute("SELECT DISTINCT event_competition_athlete_id FROM statistics_for_fights")
        existing_stats = {row[0] for row in cursor.fetchall()}
        conn.close()

        # Filter to only missing stats
        missing_stats_urls = []
        for url in stats_urls:
            # Extract IDs from URL to build the composite key
            try:
                event_id = url.split('events/')[-1].split('/')[0]
                competition_id = url.split('competitions/')[-1].split('/')[0]
                athlete_id = url.split('competitors/')[-1].split('/')[0]
                key = f"{event_id}_{competition_id}_{athlete_id}"

                if key not in existing_stats:
                    missing_stats_urls.append(url)
            except:
                missing_stats_urls.append(url)

        print(f"📊 Found {len(missing_stats_urls)} missing statistics records")

        if not missing_stats_urls:
            print("✅ No missing statistics data!")
            return

        print(f"🚀 Fetching statistics data...")

        processed = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(get_stat_data, url): url
                for url in missing_stats_urls
            }

            for future in as_completed(futures):
                url = futures[future]
                processed += 1

                if processed % 200 == 0:
                    print(f"  Progress: {processed}/{len(missing_stats_urls)}")

                try:
                    stat_data = future.result()
                    if stat_data:
                        add_to_db(stat_data, StatisticsForFight)
                        self.stats['stats_added'] += 1
                except Exception as e:
                    self.stats['errors'].append(f"Stats {url}: {e}")

        print(f"\n✅ Added statistics for {self.stats['stats_added']} fighter performances")

    # ============================================================================
    # REPORTING
    # ============================================================================

    def print_summary(self):
        """Print summary of backfill operations"""
        print("\n" + "=" * 80)
        print("BACKFILL SUMMARY")
        print("=" * 80)
        print(f"Events added:        {self.stats['events_added']}")
        print(f"Fights added:        {self.stats['fights_added']}")
        print(f"Fights updated:      {self.stats['fights_updated']}")
        print(f"Odds records added:  {self.stats['odds_added']}")
        print(f"Stats records added: {self.stats['stats_added']}")
        print(f"Errors encountered:  {len(self.stats['errors'])}")

        if self.stats['errors']:
            print("\n⚠️  Errors (first 10):")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")

        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Backfill missing MMA data")
    parser.add_argument('--events', action='store_true', help='Backfill missing events')
    parser.add_argument('--fights', action='store_true', help='Update incomplete fight results')
    parser.add_argument('--odds', action='store_true', help='Backfill missing odds')
    parser.add_argument('--stats', action='store_true', help='Backfill missing statistics')
    parser.add_argument('--all', action='store_true', help='Run all backfill operations')
    parser.add_argument('--workers', type=int, default=50, help='Number of concurrent workers')

    args = parser.parse_args()

    # If no specific flags, default to --all
    if not any([args.events, args.fights, args.odds, args.stats, args.all]):
        args.all = True

    print("🥊 MMA Data Backfiller")
    print("=" * 80)

    backfiller = DataBackfiller(max_workers=args.workers)

    if args.all or args.events:
        backfiller.backfill_missing_events()

    if args.all or args.fights:
        backfiller.update_incomplete_fights()

    if args.all or args.odds:
        backfiller.backfill_missing_odds()

    if args.all or args.stats:
        backfiller.backfill_missing_statistics()

    backfiller.print_summary()

    print("\n✅ Backfill complete!\n")


if __name__ == "__main__":
    main()
