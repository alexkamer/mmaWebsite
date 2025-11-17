"""
Script to update fighters with missing stats (0.0, --, NULL) by fetching fresh data from ESPN API
Uses multithreading for faster processing
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import requests
import time
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

DB_PATH = "data/mma.db"
ESPN_API_BASE = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/athletes/{fighter_id}"

# Thread-safe database lock
db_lock = Lock()

def get_fighters_with_missing_stats():
    """Get all fighters with missing reach, stance, or other key stats"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = """
            SELECT id, full_name, reach, stance, height, weight, age
            FROM athletes
            WHERE reach IS NULL
               OR reach = ''
               OR reach = '0.0'
               OR reach = '--'
               OR stance IS NULL
               OR stance = ''
               OR stance = '--'
            ORDER BY id
        """

        cursor.execute(query)
        fighters = cursor.fetchall()
        conn.close()

    print(f"Found {len(fighters)} fighters with missing stats")
    return fighters

def fetch_fighter_from_espn(fighter_id: int) -> Optional[Dict]:
    """Fetch fighter data from ESPN API"""
    url = ESPN_API_BASE.format(fighter_id=fighter_id)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"  Fighter {fighter_id} not found in ESPN API")
            return None
        else:
            print(f"  Error fetching fighter {fighter_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"  Exception fetching fighter {fighter_id}: {e}")
        return None

def extract_stats_from_espn_data(data: Dict) -> Dict:
    """Extract relevant stats from ESPN API response"""
    stats = {}

    # Display measurements (reach, height, weight) - check both formats
    if "displayMeasurements" in data:
        measurements = data["displayMeasurements"]
        stats["reach"] = measurements.get("reach")
        stats["height"] = measurements.get("height")
        stats["weight"] = measurements.get("weight")
    else:
        # Check for individual display fields
        if "displayReach" in data:
            # Remove the " character from reach if present (e.g., '79"' -> '79')
            reach = data["displayReach"]
            if isinstance(reach, str) and reach.endswith('"'):
                reach = reach[:-1]
            stats["reach"] = reach
        if "displayHeight" in data:
            stats["height"] = data["displayHeight"]
        if "displayWeight" in data:
            stats["weight"] = data["displayWeight"]

    # Stance - check both formats
    if "stance" in data:
        if isinstance(data["stance"], dict):
            stats["stance"] = data["stance"].get("text") or data["stance"].get("description")
        elif isinstance(data["stance"], str):
            stats["stance"] = data["stance"]

    # Age
    if "age" in data:
        stats["age"] = data["age"]

    # Headshot URL
    if "headshot" in data and "href" in data["headshot"]:
        stats["headshot_url"] = data["headshot"]["href"]

    # Team/Association
    if "citizenship" in data:
        if isinstance(data["citizenship"], dict):
            stats["association"] = data["citizenship"].get("name")
        elif isinstance(data["citizenship"], str):
            stats["association"] = data["citizenship"]

    return stats

def update_fighter_stats(fighter_id: int, stats: Dict):
    """Update fighter stats in database (thread-safe)"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build UPDATE query dynamically based on available stats
        updates = []
        values = []

        for field, value in stats.items():
            if value and value not in ['', '--', '0.0', None]:
                updates.append(f"{field} = ?")
                values.append(value)

        if not updates:
            conn.close()
            return False

        values.append(fighter_id)
        query = f"UPDATE athletes SET {', '.join(updates)} WHERE id = ?"

        try:
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"  Error updating fighter {fighter_id}: {e}")
            conn.close()
            return False

def update_single_fighter(fighter_id: int, verbose: bool = True) -> bool:
    """
    Update a single fighter's stats from ESPN API
    Returns True if successful, False otherwise
    """
    # Get current stats
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, full_name, reach, stance, height, weight, age
            FROM athletes
            WHERE id = ?
        """, (fighter_id,))
        result = cursor.fetchone()
        conn.close()

    if not result:
        if verbose:
            print(f"Fighter ID {fighter_id} not found in database")
        return False

    _, name, reach, stance, height, weight, age = result
    if verbose:
        print(f"Updating: {name} (ID: {fighter_id})")
        print(f"  Current - Reach: {reach}, Stance: {stance}")

    # Fetch from ESPN
    espn_data = fetch_fighter_from_espn(fighter_id)
    if not espn_data:
        return False

    # Extract stats
    new_stats = extract_stats_from_espn_data(espn_data)
    if not new_stats:
        if verbose:
            print(f"  No new stats found")
        return False

    if verbose:
        print(f"  New stats: {new_stats}")

    # Update database
    if update_fighter_stats(fighter_id, new_stats):
        if verbose:
            print(f"  ✓ Successfully updated")
        return True
    else:
        if verbose:
            print(f"  ✗ Failed to update")
        return False

def process_fighter_batch(fighter_data: Tuple) -> Tuple[int, str, bool]:
    """
    Process a single fighter (worker function for threading)
    Returns (fighter_id, fighter_name, success)
    """
    fighter_id, name, reach, stance, *_ = fighter_data

    # Fetch from ESPN
    espn_data = fetch_fighter_from_espn(fighter_id)
    if not espn_data:
        return (fighter_id, name, False)

    # Extract stats
    new_stats = extract_stats_from_espn_data(espn_data)
    if not new_stats:
        return (fighter_id, name, False)

    # Update database
    success = update_fighter_stats(fighter_id, new_stats)
    return (fighter_id, name, success)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Update fighter stats from ESPN API (multithreaded)')
    parser.add_argument('--fighter-id', type=int, help='Update a specific fighter by ID')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of fighters to update')
    parser.add_argument('--workers', type=int, default=10, help='Number of concurrent workers (default: 10)')

    args = parser.parse_args()

    print("=" * 60)
    print("Fighter Stats Update Script (Multithreaded)")
    print("=" * 60)

    # If specific fighter ID provided, update just that one
    if args.fighter_id:
        success = update_single_fighter(args.fighter_id, verbose=True)
        sys.exit(0 if success else 1)

    # Otherwise, update all fighters with missing stats
    fighters = get_fighters_with_missing_stats()

    if not fighters:
        print("No fighters with missing stats found!")
        return

    # Apply limit if specified
    if args.limit:
        fighters = fighters[:args.limit]
        print(f"Processing first {args.limit} fighters with {args.workers} workers")
    else:
        print(f"Processing {len(fighters)} fighters with {args.workers} workers")

    print("=" * 60)

    updated_count = 0
    error_count = 0
    start_time = time.time()

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        future_to_fighter = {
            executor.submit(process_fighter_batch, fighter): fighter
            for fighter in fighters
        }

        # Process completed tasks as they finish
        for i, future in enumerate(as_completed(future_to_fighter), 1):
            fighter_data = future_to_fighter[future]
            fighter_id, name, *_ = fighter_data

            try:
                result_id, result_name, success = future.result()

                if success:
                    updated_count += 1
                    status = "✓"
                else:
                    error_count += 1
                    status = "✗"

                # Progress indicator
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(fighters) - i) / rate if rate > 0 else 0

                print(f"[{i}/{len(fighters)}] {status} {result_name} (ID: {result_id}) | "
                      f"{rate:.1f} fighters/sec | ETA: {int(eta)}s")

            except Exception as e:
                error_count += 1
                print(f"[{i}/{len(fighters)}] ✗ {name} (ID: {fighter_id}) - Error: {e}")

    elapsed_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("Update Complete!")
    print("=" * 60)
    print(f"Total fighters processed: {len(fighters)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Errors/Not found: {error_count}")
    print(f"Time elapsed: {int(elapsed_time)}s ({elapsed_time/60:.1f} minutes)")
    print(f"Average speed: {len(fighters)/elapsed_time:.1f} fighters/sec")
    print("=" * 60)

if __name__ == "__main__":
    main()
