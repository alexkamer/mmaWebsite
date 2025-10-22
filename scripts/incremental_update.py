#!/usr/bin/env python3
"""
Incremental MMA Database Update
Fast, efficient daily/weekly update script that only checks recently active fighters
and upcoming events. This is much more efficient than the full update.

Usage:
    python scripts/incremental_update.py --days 90  # Default: check last 90 days
    python scripts/incremental_update.py --days 30  # More frequent, less comprehensive
    python scripts/incremental_update.py --days 180 # Less frequent, more comprehensive
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set, Tuple

from mma_website.utils.helpers import process_event
from archive.db import Card, Fight, Odds, StatisticsForFight, add_to_db


class IncrementalUpdater:
    """Efficient incremental database updater"""

    def __init__(self, lookback_days: int = 90):
        self.lookback_days = lookback_days
        self.cutoff_date = datetime.now() - timedelta(days=lookback_days)
        self.major_promotions = ['ufc', 'bellator', 'pfl', 'one']

        # Stats
        self.stats = {
            'fighters_checked': 0,
            'events_processed': 0,
            'fights_added': 0,
            'cards_added': 0,
            'odds_added': 0,
            'stats_added': 0
        }

    def get_recently_active_fighters(self) -> Set[int]:
        """Get fighters who fought in the last N days"""
        conn = sqlite3.connect('data/mma.db')
        cursor = conn.cursor()

        # Get fighters from recent fights
        query = f"""
        SELECT DISTINCT fighter_1_id as fighter_id
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        WHERE c.date >= datetime('now', '-{self.lookback_days} days')

        UNION

        SELECT DISTINCT fighter_2_id as fighter_id
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        WHERE c.date >= datetime('now', '-{self.lookback_days} days')
        """

        fighters = {row[0] for row in cursor.execute(query).fetchall()}
        conn.close()

        return fighters

    def get_upcoming_event_fighters(self) -> Set[int]:
        """Get fighters from upcoming events (next 30 days)"""
        conn = sqlite3.connect('data/mma.db')
        cursor = conn.cursor()

        # Get fighters from upcoming fights
        query = """
        SELECT DISTINCT fighter_1_id as fighter_id
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        WHERE c.date >= datetime('now')
        AND c.date <= datetime('now', '+30 days')

        UNION

        SELECT DISTINCT fighter_2_id as fighter_id
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        WHERE c.date >= datetime('now')
        AND c.date <= datetime('now', '+30 days')
        """

        fighters = {row[0] for row in cursor.execute(query).fetchall()}
        conn.close()

        return fighters

    def get_recent_events_from_promotions(self) -> List[Dict]:
        """Get recent and upcoming events from major promotions"""
        events = []

        for league in self.major_promotions:
            try:
                # Get events from last 30 days and next 30 days
                current_year = datetime.now().year
                years = [current_year - 1, current_year, current_year + 1]

                for year in years:
                    url = f"https://sports.core.api.espn.com/v2/sports/mma/leagues/{league}/events/?lang=en&region=us&dates={year}&limit=1000"
                    resp = httpx.get(url, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get('items', []):
                        event_ref = item.get('$ref', '')
                        if event_ref:
                            event_id = int(event_ref.split('/')[-1].split('?')[0])
                            events.append({
                                'league': league,
                                'event_id': event_id,
                                'event_url': event_ref.split('?')[0]
                            })

            except Exception as e:
                print(f"  ⚠️  Error fetching {league} events: {e}")

        return events

    def get_existing_fight_ids(self) -> Set[Tuple[str, int, str]]:
        """Get all existing (league, event_id, fight_id) combinations"""
        conn = sqlite3.connect('data/mma.db')
        cursor = conn.cursor()
        fights = set(cursor.execute("SELECT league, event_id, fight_id FROM fights").fetchall())
        conn.close()
        return fights

    def get_existing_event_ids(self) -> Set[Tuple[str, int]]:
        """Get all existing (league, event_id) combinations"""
        conn = sqlite3.connect('data/mma.db')
        cursor = conn.cursor()
        events = set(cursor.execute("SELECT league, event_id FROM cards").fetchall())
        conn.close()
        return events

    def fetch_fighter_eventlog(self, fighter_id: int) -> List[Dict]:
        """Fetch a fighter's complete eventlog"""
        url = f"https://sports.core.api.espn.com/v2/sports/mma/athletes/{fighter_id}/eventlog?lang=en&region=us&limit=300"

        try:
            resp = httpx.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            events = []
            for item in data.get('events', {}).get('items', []):
                event_ref = item.get('event', {}).get('$ref', '')
                comp_ref = item.get('competition', {}).get('$ref', '')

                if not event_ref or not comp_ref:
                    continue

                try:
                    league = comp_ref.split('leagues/')[1].split('/')[0]
                    event_id = int(comp_ref.split('events/')[1].split('/')[0])
                    comp_id = comp_ref.split('competitions/')[1].split('?')[0]

                    events.append({
                        'league': league,
                        'event_id': event_id,
                        'comp_id': comp_id,
                        'event_url': event_ref.split('?')[0]
                    })
                except (IndexError, ValueError):
                    continue

            return events

        except Exception as e:
            return []

    def find_missing_data_for_fighters(self, fighter_ids: Set[int]) -> Tuple[List[Dict], Set[Tuple[str, int]]]:
        """Find missing fights and events for a set of fighters"""
        existing_fights = self.get_existing_fight_ids()
        existing_events = self.get_existing_event_ids()

        all_missing_fights = []
        missing_events_set = set()

        print(f"  🔍 Checking {len(fighter_ids)} fighters for missing data...")

        for i, fighter_id in enumerate(fighter_ids, 1):
            if i % 50 == 0:
                print(f"    Progress: {i}/{len(fighter_ids)} fighters...")

            eventlog = self.fetch_fighter_eventlog(fighter_id)

            for event in eventlog:
                league = event['league']
                event_id = event['event_id']
                comp_id = event['comp_id']

                # Check if fight is missing
                if (league, event_id, comp_id) not in existing_fights:
                    all_missing_fights.append(event)

                    # Track missing events
                    if (league, event_id) not in existing_events:
                        missing_events_set.add((league, event_id))

        # Convert missing events set to list of dicts
        missing_events = [
            {'league': league, 'event_id': event_id}
            for league, event_id in missing_events_set
        ]

        self.stats['fighters_checked'] = len(fighter_ids)

        return all_missing_fights, missing_events

    def process_missing_events(self, missing_events: List[Dict], max_workers: int = 15):
        """Process missing events and add to database"""
        if not missing_events:
            return

        print(f"\n  📥 Processing {len(missing_events)} missing events...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Prepare event URLs
            event_urls = [
                f"http://sports.core.api.espn.com/v2/sports/mma/leagues/{e['league']}/events/{e['event_id']}?lang=en&region=us"
                for e in missing_events
            ]

            futures = {executor.submit(process_event, url): url for url in event_urls}

            for future in as_completed(futures):
                url = futures[future]
                try:
                    card, fights = future.result()

                    if card:
                        add_to_db(card, Card)
                        self.stats['cards_added'] += 1
                        self.stats['events_processed'] += 1

                    for fight in fights:
                        try:
                            # Add fight
                            add_to_db(fight, Fight)
                            self.stats['fights_added'] += 1

                            # Process odds and stats
                            if fight.get('odds_url'):
                                try:
                                    from mma_website.utils.helpers import get_odds_data
                                    odds_data = get_odds_data(fight['odds_url'])
                                    add_to_db(odds_data, Odds)
                                    self.stats['odds_added'] += 1
                                except:
                                    pass

                            # Process statistics
                            for stat_key in ['fighter_1_statistics', 'fighter_2_statistics']:
                                stat_url = fight.get(stat_key)
                                if stat_url:
                                    try:
                                        from mma_website.utils.helpers import get_stat_data
                                        stat_data = get_stat_data(stat_url)
                                        add_to_db(stat_data, StatisticsForFight)
                                        self.stats['stats_added'] += 1
                                    except:
                                        pass

                        except Exception as e:
                            print(f"    ⚠️  Error adding fight: {e}")

                except Exception as e:
                    print(f"    ⚠️  Error processing {url}: {e}")

    def run(self):
        """Run the incremental update"""
        print("\n" + "🔄" * 30)
        print("INCREMENTAL DATABASE UPDATE")
        print("🔄" * 30)
        print(f"\n📅 Checking fighters active in last {self.lookback_days} days")
        print(f"   Cutoff date: {self.cutoff_date.strftime('%Y-%m-%d')}\n")

        # Step 1: Get recently active fighters
        print("1️⃣  Getting recently active fighters...")
        recent_fighters = self.get_recently_active_fighters()
        print(f"   ✅ Found {len(recent_fighters)} recently active fighters")

        # Step 2: Get fighters from upcoming events
        print("\n2️⃣  Getting fighters from upcoming events...")
        upcoming_fighters = self.get_upcoming_event_fighters()
        print(f"   ✅ Found {len(upcoming_fighters)} fighters in upcoming events")

        # Combine and deduplicate
        all_fighters = recent_fighters | upcoming_fighters
        print(f"\n📊 Total unique fighters to check: {len(all_fighters)}")

        # Step 3: Find missing data
        print("\n3️⃣  Checking eventlogs for missing data...")
        missing_fights, missing_events = self.find_missing_data_for_fighters(all_fighters)

        print(f"\n📊 Found missing data:")
        print(f"   • {len(missing_fights)} missing fights")
        print(f"   • {len(missing_events)} missing events")

        # Step 4: Process missing events
        if missing_events:
            print("\n4️⃣  Processing missing events...")
            self.process_missing_events(missing_events)
        else:
            print("\n✅ No missing events to process!")

        # Step 5: Show summary
        print("\n" + "="*60)
        print("📊 UPDATE SUMMARY")
        print("="*60)
        print(f"Fighters checked:    {self.stats['fighters_checked']}")
        print(f"Events processed:    {self.stats['events_processed']}")
        print(f"New cards added:     {self.stats['cards_added']}")
        print(f"New fights added:    {self.stats['fights_added']}")
        print(f"New odds added:      {self.stats['odds_added']}")
        print(f"New stats added:     {self.stats['stats_added']}")
        print("="*60)
        print("\n✅ INCREMENTAL UPDATE COMPLETE!\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Efficient incremental database update using fighter eventlogs'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days to look back for recent activity (default: 90)'
    )

    args = parser.parse_args()

    try:
        updater = IncrementalUpdater(lookback_days=args.days)
        updater.run()

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
