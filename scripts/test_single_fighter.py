"""
Test script to update a single fighter with missing stats
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import requests
from pprint import pprint

DB_PATH = "data/mma.db"
FIGHTER_ID = 5296753  # Baysangur Susurkaev
ESPN_API_BASE = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/athletes/{fighter_id}"

print(f"Testing with fighter ID: {FIGHTER_ID}")
print("=" * 60)

# Get current stats
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    SELECT id, full_name, reach, stance, height, weight, age
    FROM athletes
    WHERE id = ?
""", (FIGHTER_ID,))
result = cursor.fetchone()
conn.close()

if result:
    print(f"\nCurrent stats for {result[1]}:")
    print(f"  Reach: {result[2]}")
    print(f"  Stance: {result[3]}")
    print(f"  Height: {result[4]}")
    print(f"  Weight: {result[5]}")
    print(f"  Age: {result[6]}")
else:
    print(f"Fighter {FIGHTER_ID} not found in database!")
    sys.exit(1)

# Fetch from ESPN API
print(f"\nFetching from ESPN API...")
url = ESPN_API_BASE.format(fighter_id=FIGHTER_ID)
print(f"URL: {url}")

response = requests.get(url, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\nESPN API Response:")
    print("=" * 60)

    # Display measurements
    if "displayMeasurements" in data:
        print("\nDisplay Measurements:")
        pprint(data["displayMeasurements"])

    # Stance
    if "stance" in data:
        print("\nStance:")
        pprint(data["stance"])

    # Age
    if "age" in data:
        print(f"\nAge: {data['age']}")

    # Extract stats
    stats = {}
    if "displayMeasurements" in data:
        measurements = data["displayMeasurements"]
        stats["reach"] = measurements.get("reach")
        stats["height"] = measurements.get("height")
        stats["weight"] = measurements.get("weight")

    if "stance" in data:
        stats["stance"] = data["stance"].get("text") or data["stance"].get("description")

    if "age" in data:
        stats["age"] = data["age"]

    print("\n" + "=" * 60)
    print("Extracted stats:")
    pprint(stats)

    # Ask if we should update
    print("\n" + "=" * 60)
    response = input("Update database with these values? (y/n): ")

    if response.lower() == 'y':
        updates = []
        values = []

        for field, value in stats.items():
            if value and value not in ['', '--', '0.0', None]:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.append(FIGHTER_ID)
            query = f"UPDATE athletes SET {', '.join(updates)} WHERE id = ?"

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            conn.close()

            print("\n✓ Database updated successfully!")

            # Show updated values
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, full_name, reach, stance, height, weight, age
                FROM athletes
                WHERE id = ?
            """, (FIGHTER_ID,))
            result = cursor.fetchone()
            conn.close()

            print(f"\nUpdated stats for {result[1]}:")
            print(f"  Reach: {result[2]}")
            print(f"  Stance: {result[3]}")
            print(f"  Height: {result[4]}")
            print(f"  Weight: {result[5]}")
            print(f"  Age: {result[6]}")
        else:
            print("\nNo valid stats to update")
    else:
        print("\nUpdate cancelled")

else:
    print(f"Error: Unable to fetch data (status {response.status_code})")
