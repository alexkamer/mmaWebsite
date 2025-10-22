#!/usr/bin/env python3
"""
Update MMA Database Script
Fetches the latest data from ESPN API and updates the database with:
- New leagues
- New athletes
- New events/cards
- New fights
- New odds
- New fight statistics
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
from typing import List, Dict, Tuple

from mma_website.utils.helpers import (
    get_league_urls,
    fetch_and_map_league,
    fetch_all_league_seasons,
    get_athlete_info,
    fetch_events_for_league_season,
    process_event,
    get_odds_data,
    get_stat_data
)

# Use the standalone database models from archive
from archive.db import League, Athlete, Card, Fight, Odds, StatisticsForFight, add_to_db


def get_existing_ids():
    """Fetch existing IDs from database to avoid duplicates"""
    conn = sqlite3.connect('data/mma.db')
    cursor = conn.cursor()

    league_ids = [row[0] for row in cursor.execute("SELECT id FROM leagues").fetchall()]
    athlete_ids = [row[0] for row in cursor.execute("SELECT id FROM athletes").fetchall()]
    card_ids = cursor.execute("SELECT league, event_id FROM cards").fetchall()

    conn.close()

    return league_ids, athlete_ids, card_ids


def update_leagues():
    """Update league information"""
    print("\n" + "="*60)
    print("UPDATING LEAGUES")
    print("="*60)

    league_urls = get_league_urls()
    mappings = []
    all_season_urls = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_and_map_league, url): url for url in league_urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                league_mapping, season_url = future.result()
                mappings.append(league_mapping)
                all_season_urls.append(season_url)
            except Exception as e:
                print(f"⚠️  Failed to fetch/map {url}: {e}")

    # Get existing league IDs
    league_ids, _, _ = get_existing_ids()

    # Filter new leagues
    mappings_ids = [mapping['id'] for mapping in mappings]
    new_league_ids = [id for id in mappings_ids if id not in league_ids]
    new_mappings = [mapping for mapping in mappings if mapping['id'] in new_league_ids]

    if new_mappings:
        add_to_db(new_mappings, League)
        print(f"✅ Added {len(new_mappings)} new leagues")
    else:
        print("✅ No new leagues to add")

    return all_season_urls


def update_athletes():
    """Update athlete information"""
    print("\n" + "="*60)
    print("UPDATING ATHLETES")
    print("="*60)

    BASE_URL = "https://sports.core.api.espn.com/v2/sports/mma/athletes"
    COMMON_PARAMS = {"lang": "en", "region": "us", "limit": 1000}
    MAX_WORKERS = 10

    # Fetch page count
    resp = httpx.get(BASE_URL, params=COMMON_PARAMS)
    resp.raise_for_status()
    page_count = resp.json().get("pageCount", 0)
    print(f"→ Detected {page_count} pages of athletes")

    def fetch_page(pg: int):
        params = {**COMMON_PARAMS, "page": pg}
        r = httpx.get(BASE_URL, params=params)
        r.raise_for_status()
        items = r.json().get("items", [])
        return [item.get("$ref") for item in items]

    # Fetch all athlete URLs
    all_athlete_urls = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_page, pg): pg for pg in range(1, page_count + 1)}
        for future in as_completed(futures):
            pg = futures[future]
            try:
                refs = future.result()
                all_athlete_urls.extend(refs)
            except Exception as e:
                print(f"❌ Page {pg} failed: {e!r}")

    print(f"✔ Retrieved {len(all_athlete_urls)} athlete URLs")

    # Get existing athlete IDs
    _, athlete_ids, _ = get_existing_ids()

    # Filter new athletes
    all_athlete_ids = [int(athlete.split('?')[0].split('/')[-1]) for athlete in all_athlete_urls]
    new_athlete_ids = [x for x in all_athlete_ids if x not in athlete_ids]
    new_athlete_urls = [
        f"http://sports.core.api.espn.com/v2/sports/mma/athletes/{x}?lang=en&region=us"
        for x in new_athlete_ids
    ]

    print(f"→ Found {len(new_athlete_urls)} new athletes to add")

    if new_athlete_urls:
        added_count = 0
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = {executor.submit(get_athlete_info, url): url for url in new_athlete_urls}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    athlete_data = future.result()
                    add_to_db(athlete_data, Athlete)
                    added_count += 1
                    if added_count % 100 == 0:
                        print(f"  → Added {added_count}/{len(new_athlete_urls)} athletes...")
                except Exception as e:
                    print(f"❌ Error fetching athlete data for {url}: {e}")
        print(f"✅ Added {added_count} new athletes")
    else:
        print("✅ No new athletes to add")


def update_cards_and_fights(all_season_urls):
    """Update cards (events) and fights"""
    print("\n" + "="*60)
    print("UPDATING CARDS & FIGHTS")
    print("="*60)

    league_seasons = fetch_all_league_seasons(all_season_urls)

    def get_all_event_urls(
        league_seasons: List[Dict[str, List[str]]],
        max_workers: int = 20
    ) -> List[str]:
        tasks: List[Tuple[str, str]] = []
        for mapping in league_seasons:
            for league, seasons in mapping.items():
                for season in seasons:
                    tasks.append((league, season))

        all_event_urls: List[str] = []
        with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as executor:
            future_to_task = {
                executor.submit(fetch_events_for_league_season, league, season): (league, season)
                for league, season in tasks
            }
            for future in as_completed(future_to_task):
                league, season = future_to_task[future]
                try:
                    urls = future.result()
                    all_event_urls.extend(urls)
                except Exception as exc:
                    print(f"⚠️  Error fetching {league} season {season}: {exc!r}")

        return all_event_urls

    event_urls = get_all_event_urls(league_seasons, max_workers=25)
    print(f"→ Found {len(event_urls)} total events")

    # Get existing card IDs
    _, _, card_ids = get_existing_ids()

    # Filter new cards
    all_event_ids = [
        (x.split('leagues/')[-1].split('/')[0], int(x.split('?')[0].split('/')[-1]))
        for x in event_urls
    ]
    new_card_ids = [x for x in all_event_ids if x not in card_ids]
    new_card_urls = [
        f"http://sports.core.api.espn.com/v2/sports/mma/leagues/{x[0]}/events/{x[1]}?lang=en&region=us"
        for x in new_card_ids
    ]

    print(f"→ Found {len(new_card_urls)} new cards to add")

    if not new_card_urls:
        print("✅ No new cards or fights to add")
        return [], []

    new_odds_urls = []
    new_stat_urls = []
    cards_added = 0
    fights_added = 0

    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(process_event, u): u for u in new_card_urls}
        for fut in as_completed(futures):
            url = futures[fut]
            try:
                card, evs = fut.result()
                if card:
                    add_to_db(card, Card)
                    cards_added += 1

                for ev in evs:
                    try:
                        if ev.get('odds_url'):
                            new_odds_urls.append(ev['odds_url'])
                        if ev.get('fighter_1_statistics'):
                            new_stat_urls.append(ev['fighter_1_statistics'])
                        if ev.get('fighter_2_statistics'):
                            new_stat_urls.append(ev['fighter_2_statistics'])
                        add_to_db(ev, Fight)
                        fights_added += 1
                    except Exception as e:
                        print(f"⚠️  Mapping error for event_id={ev.get('event_id')} "
                              f"league={ev.get('league')}: {e}")
            except Exception as e:
                print(f"⚠️  process_event failed for URL {url}: {e}")

    print(f"✅ Added {cards_added} new cards and {fights_added} new fights")

    return new_odds_urls, new_stat_urls


def update_odds(new_odds_urls):
    """Update betting odds"""
    print("\n" + "="*60)
    print("UPDATING ODDS")
    print("="*60)

    # Filter out None URLs
    valid_odds_urls = [url for url in new_odds_urls if url is not None]

    if not valid_odds_urls:
        print("✅ No new odds to add")
        return

    print(f"→ Found {len(valid_odds_urls)} odds URLs to process")

    added_count = 0
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(get_odds_data, url): url for url in valid_odds_urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                odds_data = future.result()
                add_to_db(odds_data, Odds)
                added_count += 1
            except Exception as e:
                print(f"❌ Error fetching odds for {url}: {e}")

    print(f"✅ Added odds for {added_count} fights")


def update_statistics(new_stat_urls):
    """Update fight statistics"""
    print("\n" + "="*60)
    print("UPDATING STATISTICS")
    print("="*60)

    # Filter out None URLs
    valid_stat_urls = [url for url in new_stat_urls if url is not None]

    if not valid_stat_urls:
        print("✅ No new statistics to add")
        return

    print(f"→ Found {len(valid_stat_urls)} statistics URLs to process")

    added_count = 0
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(get_stat_data, url): url for url in valid_stat_urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                stat_data = future.result()
                add_to_db(stat_data, StatisticsForFight)
                added_count += 1
                if added_count % 100 == 0:
                    print(f"  → Added {added_count}/{len(valid_stat_urls)} statistics...")
            except Exception as e:
                print(f"❌ Error fetching statistics for {url}: {e}")

    print(f"✅ Added {added_count} fight statistics")


def main():
    """Main function to run all updates"""
    print("\n" + "🥊" * 30)
    print("MMA DATABASE UPDATE SCRIPT")
    print("🥊" * 30)

    try:
        # Update leagues
        all_season_urls = update_leagues()

        # Update athletes
        update_athletes()

        # Update cards and fights
        new_odds_urls, new_stat_urls = update_cards_and_fights(all_season_urls)

        # Update odds
        update_odds(new_odds_urls)

        # Update statistics
        update_statistics(new_stat_urls)

        print("\n" + "="*60)
        print("✅ DATABASE UPDATE COMPLETE!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
