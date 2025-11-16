"""
Script to scrape fighter eventlog data from ESPN API.
This discovers events that may be missing from the main event scraping approach.

Each fighter's eventlog contains all their fights with URLs to:
- Event details
- Competition/fight details
- Competitor details

Usage:
    uv run python scripts/scrape_fighter_eventlogs.py
"""

import sqlite3
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import json
from pathlib import Path
import time


@dataclass
class EventLogEntry:
    """Represents a single event from a fighter's eventlog"""
    athlete_id: str
    event_id: str
    event_url: str
    competition_id: str
    competition_url: str
    competitor_url: str
    league: str
    played: bool


class FighterEventlogScraper:
    """Scrapes eventlog data for all fighters in the database"""

    BASE_URL = "https://sports.core.api.espn.com/v2/sports/mma/athletes"
    PARAMS = {"lang": "en", "region": "us", "limit": 250}

    def __init__(self, db_path: str = "data/mma.db", max_workers: int = 50):
        self.db_path = db_path
        self.max_workers = max_workers
        self.discovered_events: Set[str] = set()
        self.discovered_competitions: Set[str] = set()
        self.missing_events: Set[str] = set()
        self.missing_competitions: Set[str] = set()
        self.eventlog_entries: List[EventLogEntry] = []

    def get_all_fighter_ids(self) -> List[str]:
        """Get all athlete IDs from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Extract athlete ID from UID format: "s:3301~a:2085811" -> "2085811"
        cursor.execute("SELECT DISTINCT uid FROM athletes WHERE uid IS NOT NULL")
        uids = cursor.fetchall()
        conn.close()

        athlete_ids = []
        for (uid,) in uids:
            if uid and "~a:" in uid:
                athlete_id = uid.split("~a:")[-1]
                athlete_ids.append(athlete_id)

        return athlete_ids

    def get_existing_event_ids(self) -> Set[str]:
        """Get all event IDs already in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT event_id FROM cards WHERE event_id IS NOT NULL")
        events = {row[0] for row in cursor.fetchall()}
        conn.close()
        return events

    def get_existing_fight_ids(self) -> Set[str]:
        """Get all fight/competition IDs already in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT fight_id FROM fights WHERE fight_id IS NOT NULL")
        fights = {row[0] for row in cursor.fetchall()}
        conn.close()
        return fights

    def fetch_eventlog(self, athlete_id: str) -> Optional[List[Dict]]:
        """Fetch eventlog for a single fighter"""
        url = f"{self.BASE_URL}/{athlete_id}/eventlog"
        try:
            response = httpx.get(url, params=self.PARAMS, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            events = data.get("events", {}).get("items", [])
            return events
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Fighter has no eventlog
                return None
            print(f"❌ HTTP error {e.response.status_code} for athlete {athlete_id}")
            return None
        except Exception as e:
            print(f"❌ Error fetching eventlog for athlete {athlete_id}: {e}")
            return None

    def parse_eventlog_entry(self, athlete_id: str, event_data: Dict) -> Optional[EventLogEntry]:
        """Parse a single event entry from the eventlog"""
        try:
            event_url = event_data.get("event", {}).get("$ref", "")
            competition_url = event_data.get("competition", {}).get("$ref", "")
            competitor_url = event_data.get("competitor", {}).get("$ref", "")
            played = event_data.get("played", False)

            # Extract IDs from URLs
            # Event URL format: .../leagues/{league}/events/{event_id}?...
            # Competition URL format: .../events/{event_id}/competitions/{competition_id}?...

            if not event_url or not competition_url:
                return None

            # Parse league and event_id
            parts = event_url.split("/")
            league_idx = parts.index("leagues") if "leagues" in parts else -1
            event_idx = parts.index("events") if "events" in parts else -1

            if league_idx == -1 or event_idx == -1:
                return None

            league = parts[league_idx + 1]
            event_id = parts[event_idx + 1].split("?")[0]

            # Parse competition_id
            comp_parts = competition_url.split("/")
            comp_idx = comp_parts.index("competitions") if "competitions" in comp_parts else -1

            if comp_idx == -1:
                return None

            competition_id = comp_parts[comp_idx + 1].split("?")[0]

            return EventLogEntry(
                athlete_id=athlete_id,
                event_id=event_id,
                event_url=event_url,
                competition_id=competition_id,
                competition_url=competition_url,
                competitor_url=competitor_url,
                league=league,
                played=played
            )
        except Exception as e:
            print(f"⚠️ Error parsing eventlog entry for athlete {athlete_id}: {e}")
            return None

    def scrape_all_eventlogs(self):
        """Scrape eventlogs for all fighters"""
        print("📊 Getting fighter IDs from database...")
        athlete_ids = self.get_all_fighter_ids()
        print(f"✔ Found {len(athlete_ids)} fighters")

        print("📊 Getting existing events and fights from database...")
        existing_events = self.get_existing_event_ids()
        existing_fights = self.get_existing_fight_ids()
        print(f"✔ Found {len(existing_events)} existing events")
        print(f"✔ Found {len(existing_fights)} existing fights")

        print(f"\n🚀 Fetching eventlogs for {len(athlete_ids)} fighters (max_workers={self.max_workers})...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.fetch_eventlog, athlete_id): athlete_id
                for athlete_id in athlete_ids
            }

            completed = 0
            for future in as_completed(futures):
                athlete_id = futures[future]
                completed += 1

                if completed % 1000 == 0:
                    print(f"  Progress: {completed}/{len(athlete_ids)} fighters processed")

                try:
                    events = future.result()
                    if events:
                        for event_data in events:
                            entry = self.parse_eventlog_entry(athlete_id, event_data)
                            if entry:
                                self.eventlog_entries.append(entry)
                                self.discovered_events.add(entry.event_id)
                                self.discovered_competitions.add(entry.competition_id)

                                # Check if missing
                                if entry.event_id not in existing_events:
                                    self.missing_events.add(entry.event_id)
                                if entry.competition_id not in existing_fights:
                                    self.missing_competitions.add(entry.competition_id)
                except Exception as e:
                    print(f"❌ Error processing results for athlete {athlete_id}: {e}")

        print(f"✔ Completed scraping {len(athlete_ids)} fighters\n")

    def generate_report(self) -> str:
        """Generate a summary report"""
        report = []
        report.append("=" * 80)
        report.append("FIGHTER EVENTLOG SCRAPING REPORT")
        report.append("=" * 80)
        report.append("")

        report.append(f"📊 Total eventlog entries found: {len(self.eventlog_entries)}")
        report.append(f"📊 Unique events discovered: {len(self.discovered_events)}")
        report.append(f"📊 Unique competitions discovered: {len(self.discovered_competitions)}")
        report.append("")

        report.append(f"⚠️  Missing events (not in cards table): {len(self.missing_events)}")
        report.append(f"⚠️  Missing competitions (not in fights table): {len(self.missing_competitions)}")
        report.append("")

        # League breakdown
        league_counts = {}
        for entry in self.eventlog_entries:
            league_counts[entry.league] = league_counts.get(entry.league, 0) + 1

        report.append("📈 Events by league:")
        for league, count in sorted(league_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  - {league}: {count}")
        report.append("")

        # Sample missing events
        if self.missing_events:
            report.append("🔍 Sample missing event IDs (first 20):")
            for event_id in list(self.missing_events)[:20]:
                # Find an entry with this event
                sample_entry = next(e for e in self.eventlog_entries if e.event_id == event_id)
                report.append(f"  - {event_id} ({sample_entry.league}): {sample_entry.event_url}")
            report.append("")

        report.append("=" * 80)
        return "\n".join(report)

    def save_results(self, output_dir: str = "data"):
        """Save discovered data to JSON files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save all eventlog entries
        entries_file = output_path / "eventlog_entries.json"
        with open(entries_file, "w") as f:
            json.dump(
                [
                    {
                        "athlete_id": e.athlete_id,
                        "event_id": e.event_id,
                        "event_url": e.event_url,
                        "competition_id": e.competition_id,
                        "competition_url": e.competition_url,
                        "competitor_url": e.competitor_url,
                        "league": e.league,
                        "played": e.played
                    }
                    for e in self.eventlog_entries
                ],
                f,
                indent=2
            )
        print(f"✔ Saved eventlog entries to {entries_file}")

        # Save missing events
        missing_events_file = output_path / "missing_events.json"
        with open(missing_events_file, "w") as f:
            json.dump(list(self.missing_events), f, indent=2)
        print(f"✔ Saved missing event IDs to {missing_events_file}")

        # Save missing competitions
        missing_comps_file = output_path / "missing_competitions.json"
        with open(missing_comps_file, "w") as f:
            json.dump(list(self.missing_competitions), f, indent=2)
        print(f"✔ Saved missing competition IDs to {missing_comps_file}")

        # Save report
        report_file = output_path / "eventlog_scraping_report.txt"
        with open(report_file, "w") as f:
            f.write(self.generate_report())
        print(f"✔ Saved report to {report_file}")


def main():
    """Main execution function"""
    print("\n🥊 MMA Fighter Eventlog Scraper")
    print("=" * 80)

    scraper = FighterEventlogScraper(
        db_path="data/mma.db",
        max_workers=75  # Adjust based on your system and rate limits
    )

    # Scrape all eventlogs
    scraper.scrape_all_eventlogs()

    # Generate and print report
    report = scraper.generate_report()
    print("\n" + report)

    # Save results
    print("\n💾 Saving results...")
    scraper.save_results()

    print("\n✅ Done!\n")


if __name__ == "__main__":
    main()
