"""
Add database indexes for performance optimization
Run this script to add indexes to commonly queried columns
"""

import sqlite3
import os

def add_indexes():
    """Add performance indexes to the database"""

    # Get database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mma.db')

    print(f"📊 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List of indexes to create
    indexes = [
        # Athletes table - search and filter optimization
        ("idx_athletes_full_name", "CREATE INDEX IF NOT EXISTS idx_athletes_full_name ON athletes(full_name)"),
        ("idx_athletes_default_league", "CREATE INDEX IF NOT EXISTS idx_athletes_default_league ON athletes(default_league)"),
        ("idx_athletes_weight_class", "CREATE INDEX IF NOT EXISTS idx_athletes_weight_class ON athletes(weight_class)"),
        ("idx_athletes_league_name", "CREATE INDEX IF NOT EXISTS idx_athletes_league_name ON athletes(default_league, full_name)"),

        # Fights table - join and filter optimization
        ("idx_fights_event_id", "CREATE INDEX IF NOT EXISTS idx_fights_event_id ON fights(event_id)"),
        ("idx_fights_fighter_1_id", "CREATE INDEX IF NOT EXISTS idx_fights_fighter_1_id ON fights(fighter_1_id)"),
        ("idx_fights_fighter_2_id", "CREATE INDEX IF NOT EXISTS idx_fights_fighter_2_id ON fights(fighter_2_id)"),
        ("idx_fights_league", "CREATE INDEX IF NOT EXISTS idx_fights_league ON fights(league)"),
        ("idx_fights_weight_class", "CREATE INDEX IF NOT EXISTS idx_fights_weight_class ON fights(weight_class)"),
        ("idx_fights_fighter_1_winner", "CREATE INDEX IF NOT EXISTS idx_fights_fighter_1_winner ON fights(fighter_1_winner)"),
        ("idx_fights_fighter_2_winner", "CREATE INDEX IF NOT EXISTS idx_fights_fighter_2_winner ON fights(fighter_2_winner)"),

        # Cards table - date and league filtering
        ("idx_cards_event_id", "CREATE INDEX IF NOT EXISTS idx_cards_event_id ON cards(event_id)"),
        ("idx_cards_date", "CREATE INDEX IF NOT EXISTS idx_cards_date ON cards(date)"),
        ("idx_cards_league", "CREATE INDEX IF NOT EXISTS idx_cards_league ON cards(league)"),
        ("idx_cards_league_date", "CREATE INDEX IF NOT EXISTS idx_cards_league_date ON cards(league, date)"),

        # Odds table - join optimization
        ("idx_odds_fight_id", "CREATE INDEX IF NOT EXISTS idx_odds_fight_id ON odds(fight_id)"),
        ("idx_odds_home_athlete", "CREATE INDEX IF NOT EXISTS idx_odds_home_athlete ON odds(home_athlete_id)"),
        ("idx_odds_away_athlete", "CREATE INDEX IF NOT EXISTS idx_odds_away_athlete ON odds(away_athlete_id)"),

        # UFC Rankings - filter optimization
        ("idx_rankings_division", "CREATE INDEX IF NOT EXISTS idx_rankings_division ON ufc_rankings(division)"),
        ("idx_rankings_fighter_name", "CREATE INDEX IF NOT EXISTS idx_rankings_fighter_name ON ufc_rankings(fighter_name)"),
        ("idx_rankings_ranking_type", "CREATE INDEX IF NOT EXISTS idx_rankings_ranking_type ON ufc_rankings(ranking_type)"),
    ]

    # Create each index
    created_count = 0
    skipped_count = 0

    for index_name, create_statement in indexes:
        try:
            cursor.execute(create_statement)
            created_count += 1
            print(f"✅ Created index: {index_name}")
        except sqlite3.Error as e:
            if "already exists" in str(e):
                skipped_count += 1
                print(f"⏭️  Skipped (exists): {index_name}")
            else:
                print(f"❌ Error creating {index_name}: {e}")

    # Commit changes
    conn.commit()

    # Run ANALYZE to update query planner statistics
    print("\n📈 Running ANALYZE to update query statistics...")
    cursor.execute("ANALYZE")
    conn.commit()

    # Show database statistics
    cursor.execute("SELECT page_count * page_size / 1024.0 / 1024.0 as size_mb FROM pragma_page_count(), pragma_page_size();")
    size_mb = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    total_indexes = cursor.fetchone()[0]

    print(f"\n📊 Database Statistics:")
    print(f"   Database size: {size_mb:.2f} MB")
    print(f"   Total indexes: {total_indexes}")
    print(f"   Indexes created: {created_count}")
    print(f"   Indexes skipped: {skipped_count}")

    conn.close()
    print("\n✅ Index optimization complete!")

if __name__ == "__main__":
    add_indexes()
