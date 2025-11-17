"""
Script to update fighters with missing stats (0.0, --, NULL) by fetching fresh data from ESPN API
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import requests
import time
from typing import Optional, Dict

DB_PATH = "data/mma.db"
ESPN_API_BASE = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/athletes/{fighter_id}"

def get_fighters_with_missing_stats():
    """Get all fighters with missing reach, stance, or other key stats"""
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

    # Display measurements (reach, height, weight)
    if "displayMeasurements" in data:
        measurements = data["displayMeasurements"]
        stats["reach"] = measurements.get("reach")
        stats["height"] = measurements.get("height")
        stats["weight"] = measurements.get("weight")

    # Stance
    if "stance" in data:
        stats["stance"] = data["stance"].get("text") or data["stance"].get("description")

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
    """Update fighter stats in database"""
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

def update_single_fighter(fighter_id: int) -> bool:
    """
    Update a single fighter's stats from ESPN API
    Returns True if successful, False otherwise
    """
    # Get current stats
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
        print(f"Fighter ID {fighter_id} not found in database")
        return False

    _, name, reach, stance, height, weight, age = result
    print(f"Updating: {name} (ID: {fighter_id})")
    print(f"  Current - Reach: {reach}, Stance: {stance}")

    # Fetch from ESPN
    espn_data = fetch_fighter_from_espn(fighter_id)
    if not espn_data:
        return False

    # Extract stats
    new_stats = extract_stats_from_espn_data(espn_data)
    if not new_stats:
        print(f"  No new stats found")
        return False

    print(f"  New stats: {new_stats}")

    # Update database
    if update_fighter_stats(fighter_id, new_stats):
        print(f"  ✓ Successfully updated")
        return True
    else:
        print(f"  ✗ Failed to update")
        return False

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Update fighter stats from ESPN API')
    parser.add_argument('--fighter-id', type=int, help='Update a specific fighter by ID')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of fighters to update')

    args = parser.parse_args()

    print("=" * 60)
    print("Fighter Stats Update Script")
    print("=" * 60)

    # If specific fighter ID provided, update just that one
    if args.fighter_id:
        success = update_single_fighter(args.fighter_id)
        sys.exit(0 if success else 1)

    # Otherwise, update all fighters with missing stats
    fighters = get_fighters_with_missing_stats()

    if not fighters:
        print("No fighters with missing stats found!")
        return

    # Apply limit if specified
    if args.limit:
        fighters = fighters[:args.limit]
        print(f"Processing first {args.limit} fighters")

    updated_count = 0
    not_found_count = 0
    error_count = 0

    for i, (fighter_id, name, reach, stance, height, weight, age) in enumerate(fighters, 1):
        print(f"\n[{i}/{len(fighters)}] Processing: {name} (ID: {fighter_id})")
        print(f"  Current stats - Reach: {reach}, Stance: {stance}")

        # Fetch fresh data from ESPN
        espn_data = fetch_fighter_from_espn(fighter_id)

        if espn_data is None:
            not_found_count += 1
            time.sleep(0.5)  # Rate limiting
            continue

        # Extract stats
        new_stats = extract_stats_from_espn_data(espn_data)

        if not new_stats:
            print(f"  No new stats found for {name}")
            error_count += 1
            time.sleep(0.5)
            continue

        print(f"  New stats found: {new_stats}")

        # Update database
        if update_fighter_stats(fighter_id, new_stats):
            updated_count += 1
            print(f"  ✓ Updated {name}")
        else:
            error_count += 1
            print(f"  ✗ Failed to update {name}")

        # Rate limiting - be nice to ESPN API
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("Update Complete!")
    print("=" * 60)
    print(f"Total fighters processed: {len(fighters)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Not found in ESPN: {not_found_count}")
    print(f"Errors: {error_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
