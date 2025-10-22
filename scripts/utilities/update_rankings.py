#!/usr/bin/env python3
"""
Simple UFC Rankings Update Script

Updates the database with current UFC champions and rankings.
This version uses known current data as a reliable fallback.

Usage:
    python scripts/utilities/update_rankings.py
"""

import sqlite3
from datetime import datetime
import sys
import os

# Add the parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def update_ufc_rankings():
    """Update UFC rankings with current data (as of Dec 2024)"""

    # Current UFC Champions and Top Contenders (accurate as of Dec 2024)
    rankings_data = [
        # MEN'S DIVISION CHAMPIONS
        {'division': 'Heavyweight', 'fighter_name': 'Jon Jones', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Alex Pereira', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Dricus Du Plessis', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Belal Muhammad', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Islam Makhachev', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Ilia Topuria', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Merab Dvalishvili', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Alexandre Pantoja', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},

        # WOMEN'S DIVISION CHAMPIONS
        {'division': "Women's Bantamweight", 'fighter_name': 'Raquel Pennington', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Valentina Shevchenko', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Zhang Weili', 'rank': 0, 'is_champion': True, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},

        # MEN'S P4P TOP 10
        {'division': "Men's P4P", 'fighter_name': 'Islam Makhachev', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Jon Jones', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Alex Pereira', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Ilia Topuria', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Dricus Du Plessis', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Belal Muhammad', 'rank': 6, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Merab Dvalishvili', 'rank': 7, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Alexandre Pantoja', 'rank': 8, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Sean Strickland', 'rank': 9, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},
        {'division': "Men's P4P", 'fighter_name': 'Kamaru Usman', 'rank': 10, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'P4P'},

        # WOMEN'S P4P TOP 5
        {'division': "Women's P4P", 'fighter_name': 'Valentina Shevchenko', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'P4P'},
        {'division': "Women's P4P", 'fighter_name': 'Zhang Weili', 'rank': 2, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'P4P'},
        {'division': "Women's P4P", 'fighter_name': 'Raquel Pennington', 'rank': 3, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'P4P'},
        {'division': "Women's P4P", 'fighter_name': 'Alexa Grasso', 'rank': 4, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'P4P'},
        {'division': "Women's P4P", 'fighter_name': 'Tatiana Suarez', 'rank': 5, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'P4P'},

        # TOP CONTENDERS (Rank #1 in each division)
        {'division': 'Heavyweight', 'fighter_name': 'Stipe Miocic', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Light Heavyweight', 'fighter_name': 'Magomed Ankalaev', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Middleweight', 'fighter_name': 'Sean Strickland', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Welterweight', 'fighter_name': 'Shavkat Rakhmonov', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Lightweight', 'fighter_name': 'Arman Tsarukyan', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Featherweight', 'fighter_name': 'Alexander Volkanovski', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Bantamweight', 'fighter_name': 'Umar Nurmagomedov', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': 'Flyweight', 'fighter_name': 'Kai Kara-France', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'M', 'ranking_type': 'Division'},
        {'division': "Women's Bantamweight", 'fighter_name': 'Ketlen Vieira', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Flyweight", 'fighter_name': 'Alexa Grasso', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
        {'division': "Women's Strawweight", 'fighter_name': 'Tatiana Suarez', 'rank': 1, 'is_champion': False, 'is_interim_champion': False, 'gender': 'F', 'ranking_type': 'Division'},
    ]

    db_path = "data/mma.db"

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False

    try:
        print("🚀 Updating UFC Rankings...")
        print("=" * 40)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Clear existing rankings
        cursor.execute("DELETE FROM ufc_rankings")
        print("🗑️ Cleared existing rankings")

        # Insert new rankings
        inserted_count = 0
        champions_count = 0

        for ranking in rankings_data:
            cursor.execute("""
                INSERT INTO ufc_rankings
                (division, fighter_name, rank, is_champion, is_interim_champion,
                 gender, ranking_type, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ranking['division'],
                ranking['fighter_name'],
                ranking['rank'],
                ranking['is_champion'],
                ranking['is_interim_champion'],
                ranking['gender'],
                ranking['ranking_type'],
                datetime.now()
            ))

            if ranking['is_champion']:
                champions_count += 1
            inserted_count += 1

        conn.commit()
        conn.close()

        print(f"✅ Successfully updated database:")
        print(f"   📊 {inserted_count} total entries")
        print(f"   🏆 {champions_count} champions")
        print(f"   👑 {len([r for r in rankings_data if r['ranking_type'] == 'P4P'])} P4P rankings")
        print("=" * 40)
        print("🏁 Rankings update completed successfully!")

        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    success = update_ufc_rankings()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()