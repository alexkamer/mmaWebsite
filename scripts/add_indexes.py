"""
Script to add database indexes for optimizing common queries.
Run this to improve query performance on the MMA database.
"""
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

DATABASE_PATH = "data/mma.db"

# Index definitions for common queries
INDEXES = [
    # Athletes table indexes
    ("idx_athletes_full_name", "CREATE INDEX IF NOT EXISTS idx_athletes_full_name ON athletes(full_name COLLATE NOCASE)"),
    ("idx_athletes_display_name", "CREATE INDEX IF NOT EXISTS idx_athletes_display_name ON athletes(display_name COLLATE NOCASE)"),
    ("idx_athletes_weight_class", "CREATE INDEX IF NOT EXISTS idx_athletes_weight_class ON athletes(weight_class)"),
    ("idx_athletes_active", "CREATE INDEX IF NOT EXISTS idx_athletes_active ON athletes(is_active)"),

    # Fights table indexes
    ("idx_fights_fighter_1_id", "CREATE INDEX IF NOT EXISTS idx_fights_fighter_1_id ON fights(fighter_1_id)"),
    ("idx_fights_fighter_2_id", "CREATE INDEX IF NOT EXISTS idx_fights_fighter_2_id ON fights(fighter_2_id)"),
    ("idx_fights_event_id", "CREATE INDEX IF NOT EXISTS idx_fights_event_id ON fights(event_id)"),
    ("idx_fights_event_league", "CREATE INDEX IF NOT EXISTS idx_fights_event_league ON fights(event_id, league)"),
    ("idx_fights_weight_class", "CREATE INDEX IF NOT EXISTS idx_fights_weight_class ON fights(weight_class)"),

    # Cards table indexes
    ("idx_cards_date", "CREATE INDEX IF NOT EXISTS idx_cards_date ON cards(date DESC)"),
    ("idx_cards_event_id", "CREATE INDEX IF NOT EXISTS idx_cards_event_id ON cards(event_id)"),
    ("idx_cards_league", "CREATE INDEX IF NOT EXISTS idx_cards_league ON cards(league)"),
    ("idx_cards_year_league", "CREATE INDEX IF NOT EXISTS idx_cards_year_league ON cards(league, date)"),

    # Odds table indexes
    ("idx_odds_fight_id", "CREATE INDEX IF NOT EXISTS idx_odds_fight_id ON odds(fight_id)"),
    ("idx_odds_away_athlete", "CREATE INDEX IF NOT EXISTS idx_odds_away_athlete ON odds(away_athlete_id)"),
    ("idx_odds_home_athlete", "CREATE INDEX IF NOT EXISTS idx_odds_home_athlete ON odds(home_athlete_id)"),

    # UFC Rankings table indexes (if it exists)
    ("idx_ufc_rankings_division", "CREATE INDEX IF NOT EXISTS idx_ufc_rankings_division ON ufc_rankings(division)"),
    ("idx_ufc_rankings_fighter_name", "CREATE INDEX IF NOT EXISTS idx_ufc_rankings_fighter_name ON ufc_rankings(fighter_name COLLATE NOCASE)"),
    ("idx_ufc_rankings_champion", "CREATE INDEX IF NOT EXISTS idx_ufc_rankings_champion ON ufc_rankings(is_champion)"),
]

def add_indexes():
    """Add indexes to the database."""
    print(f"Connecting to database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print(f"\nAdding {len(INDEXES)} indexes...")
    success_count = 0

    for index_name, sql in INDEXES:
        try:
            print(f"  Creating {index_name}...", end=" ")
            cursor.execute(sql)
            print("✓")
            success_count += 1
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print("(already exists)")
                success_count += 1
            elif "no such table" in str(e):
                print("(table does not exist, skipping)")
            else:
                print(f"✗ Error: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")

    conn.commit()
    conn.close()

    print(f"\nSuccessfully added/verified {success_count}/{len(INDEXES)} indexes")
    print("Database optimization complete!")

def analyze_database():
    """Run ANALYZE to update query planner statistics."""
    print("\nRunning ANALYZE to update query planner statistics...")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("ANALYZE")
        conn.commit()
        print("✓ ANALYZE complete")
    except Exception as e:
        print(f"✗ Error running ANALYZE: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MMA Database Index Optimization")
    print("=" * 60)

    try:
        add_indexes()
        analyze_database()
        print("\n" + "=" * 60)
        print("Optimization complete! Database queries should be faster now.")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
