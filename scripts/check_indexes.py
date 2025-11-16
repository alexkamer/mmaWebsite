#!/usr/bin/env python3
"""Script to check database indexes and performance"""
import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_indexes():
    """Check what indexes exist in the database"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mma.db')

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("📊 Database Indexes Report\n")
    print("=" * 80)

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    total_indexes = 0
    for (table_name,) in tables:
        # Get indexes for this table
        cursor.execute(f"SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
        indexes = cursor.fetchall()

        if indexes:
            print(f"\n📁 Table: {table_name}")
            print(f"   Indexes: {len(indexes)}")
            for idx_name, idx_sql in indexes:
                if idx_sql:  # Skip auto-created indexes
                    print(f"   - {idx_name}")
            total_indexes += len(indexes)

    print("\n" + "=" * 80)
    print(f"\n✅ Total indexes: {total_indexes}")
    print(f"✅ Total tables: {len(tables)}")

    # Check database size
    db_size = os.path.getsize(db_path)
    print(f"💾 Database size: {db_size / (1024*1024):.2f} MB")

    conn.close()

if __name__ == "__main__":
    check_indexes()
