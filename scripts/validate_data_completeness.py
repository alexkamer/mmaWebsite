"""
Data validation and completeness checking script.

Analyzes the database to identify:
- Data gaps and missing records
- Incomplete fight results
- Orphaned records
- Data quality issues

Usage:
    uv run python scripts/validate_data_completeness.py
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json


class DataValidator:
    """Validates data completeness and quality in the MMA database"""

    def __init__(self, db_path: str = "data/mma.db"):
        self.db_path = db_path
        self.issues = []
        self.stats = {}

    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def run_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a query and return results"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

    def get_single_value(self, query: str, params: tuple = ()) -> any:
        """Execute a query and return a single value"""
        results = self.run_query(query, params)
        return results[0][0] if results else None

    # ============================================================================
    # BASIC STATS
    # ============================================================================

    def collect_basic_stats(self):
        """Collect basic statistics about the database"""
        print("\n" + "=" * 80)
        print("DATABASE OVERVIEW")
        print("=" * 80)

        # Counts
        self.stats['total_athletes'] = self.get_single_value("SELECT COUNT(*) FROM athletes")
        self.stats['total_events'] = self.get_single_value("SELECT COUNT(*) FROM cards")
        self.stats['total_fights'] = self.get_single_value("SELECT COUNT(*) FROM fights")
        self.stats['total_odds'] = self.get_single_value("SELECT COUNT(*) FROM odds")
        self.stats['total_statistics'] = self.get_single_value("SELECT COUNT(*) FROM statistics_for_fights")

        print(f"Athletes:     {self.stats['total_athletes']:,}")
        print(f"Events:       {self.stats['total_events']:,}")
        print(f"Fights:       {self.stats['total_fights']:,}")
        print(f"Odds records: {self.stats['total_odds']:,}")
        print(f"Statistics:   {self.stats['total_statistics']:,}")

        # Events by league
        print("\n📊 Events by league:")
        league_counts = self.run_query("""
            SELECT league, COUNT(*) as count
            FROM cards
            GROUP BY league
            ORDER BY count DESC
        """)
        for league, count in league_counts:
            print(f"  - {league}: {count:,}")

        # Events by year
        print("\n📊 Events by year (last 10 years):")
        year_counts = self.run_query("""
            SELECT strftime('%Y', date) as year, COUNT(*) as count
            FROM cards
            WHERE date >= date('now', '-10 years')
            GROUP BY year
            ORDER BY year DESC
        """)
        for year, count in year_counts:
            print(f"  - {year}: {count:,}")

    # ============================================================================
    # MISSING RESULTS
    # ============================================================================

    def check_missing_results(self):
        """Check for fights that should have results but don't"""
        print("\n" + "=" * 80)
        print("MISSING FIGHT RESULTS")
        print("=" * 80)

        # Fights with NULL winners from past events
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        incomplete_fights = self.get_single_value("""
            SELECT COUNT(*)
            FROM fights
            WHERE fighter_1_winner IS NULL
              AND fighter_2_winner IS NULL
              AND date(date) < date(?)
        """, (cutoff_date,))

        print(f"⚠️  Fights with missing results (>7 days old): {incomplete_fights:,}")

        if incomplete_fights > 0:
            self.issues.append({
                'type': 'missing_results',
                'count': incomplete_fights,
                'severity': 'medium'
            })

            # Sample events with incomplete results
            sample = self.run_query("""
                SELECT DISTINCT event_id, league, date(date) as fight_date
                FROM fights
                WHERE fighter_1_winner IS NULL
                  AND fighter_2_winner IS NULL
                  AND date(date) < date(?)
                ORDER BY date DESC
                LIMIT 10
            """, (cutoff_date,))

            print(f"\n📋 Sample events with missing results:")
            for event_id, league, fight_date in sample:
                print(f"  - Event {event_id} ({league}) on {fight_date}")

    # ============================================================================
    # MISSING ODDS
    # ============================================================================

    def check_missing_odds(self):
        """Check for fights with odds URLs but no odds data"""
        print("\n" + "=" * 80)
        print("MISSING ODDS DATA")
        print("=" * 80)

        total_with_odds_url = self.get_single_value("""
            SELECT COUNT(*)
            FROM fights
            WHERE odds_url IS NOT NULL
        """)

        fights_with_odds_data = self.get_single_value("""
            SELECT COUNT(DISTINCT f.fight_id)
            FROM fights f
            INNER JOIN odds o ON f.fight_id = o.fight_id
        """)

        missing_odds = total_with_odds_url - fights_with_odds_data if fights_with_odds_data else total_with_odds_url

        print(f"Total fights with odds_url:     {total_with_odds_url:,}")
        print(f"Fights with actual odds data:   {fights_with_odds_data:,}")
        print(f"⚠️  Missing odds data:            {missing_odds:,}")

        if missing_odds > 0:
            coverage_pct = (fights_with_odds_data / total_with_odds_url * 100) if total_with_odds_url > 0 else 0
            print(f"Odds coverage: {coverage_pct:.1f}%")

            self.issues.append({
                'type': 'missing_odds',
                'count': missing_odds,
                'severity': 'low'
            })

    # ============================================================================
    # MISSING STATISTICS
    # ============================================================================

    def check_missing_statistics(self):
        """Check for fights with statistics URLs but no statistics data"""
        print("\n" + "=" * 80)
        print("MISSING STATISTICS DATA")
        print("=" * 80)

        # Count total stat URLs (both fighter 1 and fighter 2)
        total_stat_urls = self.get_single_value("""
            SELECT
                (SELECT COUNT(*) FROM fights WHERE fighter_1_statistics IS NOT NULL) +
                (SELECT COUNT(*) FROM fights WHERE fighter_2_statistics IS NOT NULL)
        """)

        total_stats_records = self.get_single_value("""
            SELECT COUNT(*)
            FROM statistics_for_fights
        """)

        missing_stats = total_stat_urls - total_stats_records if total_stats_records else total_stat_urls

        print(f"Total stat URLs in fights:      {total_stat_urls:,}")
        print(f"Actual statistics records:      {total_stats_records:,}")
        print(f"⚠️  Missing statistics data:      {missing_stats:,}")

        if missing_stats > 0:
            coverage_pct = (total_stats_records / total_stat_urls * 100) if total_stat_urls > 0 else 0
            print(f"Statistics coverage: {coverage_pct:.1f}%")

            self.issues.append({
                'type': 'missing_statistics',
                'count': missing_stats,
                'severity': 'low'
            })

    # ============================================================================
    # ORPHANED RECORDS
    # ============================================================================

    def check_orphaned_records(self):
        """Check for orphaned records (fights without events, etc.)"""
        print("\n" + "=" * 80)
        print("ORPHANED RECORDS")
        print("=" * 80)

        # Fights without corresponding events
        orphaned_fights = self.get_single_value("""
            SELECT COUNT(*)
            FROM fights f
            LEFT JOIN cards c ON f.event_id = c.event_id
            WHERE c.event_id IS NULL
        """)

        print(f"Fights without parent events:   {orphaned_fights:,}")

        if orphaned_fights > 0:
            self.issues.append({
                'type': 'orphaned_fights',
                'count': orphaned_fights,
                'severity': 'high'
            })

        # Odds without corresponding fights
        orphaned_odds = self.get_single_value("""
            SELECT COUNT(*)
            FROM odds o
            LEFT JOIN fights f ON o.fight_id = f.fight_id
            WHERE f.fight_id IS NULL
        """)

        print(f"Odds without parent fights:     {orphaned_odds:,}")

        if orphaned_odds > 0:
            self.issues.append({
                'type': 'orphaned_odds',
                'count': orphaned_odds,
                'severity': 'medium'
            })

        # Statistics without corresponding fights
        orphaned_stats = self.get_single_value("""
            SELECT COUNT(*)
            FROM statistics_for_fights s
            LEFT JOIN fights f ON s.competition_id = f.fight_id
            WHERE f.fight_id IS NULL
        """)

        print(f"Statistics without parent fights: {orphaned_stats:,}")

        if orphaned_stats > 0:
            self.issues.append({
                'type': 'orphaned_statistics',
                'count': orphaned_stats,
                'severity': 'medium'
            })

    # ============================================================================
    # DATA QUALITY
    # ============================================================================

    def check_data_quality(self):
        """Check for data quality issues"""
        print("\n" + "=" * 80)
        print("DATA QUALITY CHECKS")
        print("=" * 80)

        # Athletes without names
        athletes_no_name = self.get_single_value("""
            SELECT COUNT(*)
            FROM athletes
            WHERE (first_name IS NULL OR first_name = '')
              AND (last_name IS NULL OR last_name = '')
              AND (display_name IS NULL OR display_name = '')
        """)
        print(f"Athletes without names:         {athletes_no_name:,}")

        # Events without dates
        events_no_date = self.get_single_value("""
            SELECT COUNT(*)
            FROM cards
            WHERE date IS NULL
        """)
        print(f"Events without dates:           {events_no_date:,}")

        # Fights with invalid fighter IDs
        fights_invalid_fighters = self.get_single_value("""
            SELECT COUNT(*)
            FROM fights
            WHERE fighter_1_id IS NULL OR fighter_2_id IS NULL
        """)
        print(f"Fights with invalid fighter IDs: {fights_invalid_fighters:,}")

        # Check for duplicate fight records
        duplicate_fights = self.get_single_value("""
            SELECT COUNT(*) - COUNT(DISTINCT fight_id)
            FROM fights
        """)
        print(f"Duplicate fight records:        {duplicate_fights:,}")

        if any([athletes_no_name, events_no_date, fights_invalid_fighters, duplicate_fights]):
            self.issues.append({
                'type': 'data_quality',
                'details': {
                    'athletes_no_name': athletes_no_name,
                    'events_no_date': events_no_date,
                    'fights_invalid_fighters': fights_invalid_fighters,
                    'duplicate_fights': duplicate_fights
                },
                'severity': 'medium'
            })

    # ============================================================================
    # COMPLETENESS BY LEAGUE
    # ============================================================================

    def check_completeness_by_league(self):
        """Check data completeness broken down by league"""
        print("\n" + "=" * 80)
        print("COMPLETENESS BY LEAGUE")
        print("=" * 80)

        leagues = self.run_query("""
            SELECT DISTINCT league FROM fights ORDER BY league
        """)

        for (league,) in leagues:
            total_fights = self.get_single_value("""
                SELECT COUNT(*) FROM fights WHERE league = ?
            """, (league,))

            completed_fights = self.get_single_value("""
                SELECT COUNT(*) FROM fights
                WHERE league = ?
                  AND (fighter_1_winner IS NOT NULL OR fighter_2_winner IS NOT NULL)
            """, (league,))

            fights_with_odds = self.get_single_value("""
                SELECT COUNT(DISTINCT f.fight_id)
                FROM fights f
                INNER JOIN odds o ON f.fight_id = o.fight_id
                WHERE f.league = ?
            """, (league,))

            fights_with_stats = self.get_single_value("""
                SELECT COUNT(DISTINCT f.fight_id)
                FROM fights f
                INNER JOIN statistics_for_fights s ON f.fight_id = s.competition_id
                WHERE f.league = ?
            """, (league,))

            completion_pct = (completed_fights / total_fights * 100) if total_fights > 0 else 0
            odds_pct = (fights_with_odds / total_fights * 100) if total_fights > 0 else 0
            stats_pct = (fights_with_stats / total_fights * 100) if total_fights > 0 else 0

            print(f"\n📊 {league.upper()}:")
            print(f"  Total fights:      {total_fights:,}")
            print(f"  With results:      {completed_fights:,} ({completion_pct:.1f}%)")
            print(f"  With odds:         {fights_with_odds:,} ({odds_pct:.1f}%)")
            print(f"  With statistics:   {fights_with_stats:,} ({stats_pct:.1f}%)")

    # ============================================================================
    # SUMMARY
    # ============================================================================

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        if not self.issues:
            print("✅ No critical issues found!")
        else:
            high_severity = sum(1 for i in self.issues if i['severity'] == 'high')
            medium_severity = sum(1 for i in self.issues if i['severity'] == 'medium')
            low_severity = sum(1 for i in self.issues if i['severity'] == 'low')

            print(f"Total issues found: {len(self.issues)}")
            print(f"  🔴 High severity:   {high_severity}")
            print(f"  🟡 Medium severity: {medium_severity}")
            print(f"  🟢 Low severity:    {low_severity}")

            print("\n📋 Issue breakdown:")
            for issue in self.issues:
                severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[issue['severity']]
                count = issue.get('count', 'N/A')
                print(f"  {severity_emoji} {issue['type']}: {count}")

        print("\n💡 Recommendations:")
        if any(i['type'] == 'missing_results' for i in self.issues):
            print("  - Run: uv run python scripts/backfill_missing_data.py --fights")
        if any(i['type'] == 'missing_odds' for i in self.issues):
            print("  - Run: uv run python scripts/backfill_missing_data.py --odds")
        if any(i['type'] == 'missing_statistics' for i in self.issues):
            print("  - Run: uv run python scripts/backfill_missing_data.py --stats")
        if any(i['type'].startswith('orphaned') for i in self.issues):
            print("  - Investigate orphaned records manually")

        print("=" * 80)

    def run_all_checks(self):
        """Run all validation checks"""
        self.collect_basic_stats()
        self.check_missing_results()
        self.check_missing_odds()
        self.check_missing_statistics()
        self.check_orphaned_records()
        self.check_data_quality()
        self.check_completeness_by_league()
        self.print_summary()


def main():
    print("🥊 MMA Database Validator")
    print("=" * 80)

    validator = DataValidator()
    validator.run_all_checks()

    print("\n✅ Validation complete!\n")


if __name__ == "__main__":
    main()
