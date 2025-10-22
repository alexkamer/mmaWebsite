#!/usr/bin/env python3
"""
Accurate UFC Rankings Scraper

Based on actual HTML structure analysis. Correctly identifies champions and rankings
from the UFC.com rankings page.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
from datetime import datetime
import sys
import os

# Add the parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class AccurateUFCRankingsScraper:
    def __init__(self, db_path="data/mma.db"):
        self.db_path = db_path
        self.base_url = "https://www.ufc.com/rankings"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def fetch_rankings_page(self):
        """Fetch the UFC rankings page"""
        try:
            print("🌐 Fetching UFC rankings page...")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"✅ Successfully fetched page ({len(response.text)} chars)")
            return soup

        except requests.RequestException as e:
            print(f"❌ Error fetching page: {e}")
            return None

    def extract_rankings_data(self, soup):
        """Extract rankings using the correct table structure"""
        rankings_data = []

        # Find all ranking tables using the view-grouping pattern
        view_groupings = soup.find_all('div', class_='view-grouping')

        for grouping in view_groupings:
            # Get division name from header
            header = grouping.find('div', class_='view-grouping-header')
            if not header:
                continue

            division_name = header.get_text(strip=True)
            division_name = self.clean_division_name(division_name)

            # Find the table
            table = grouping.find('table')
            if not table:
                continue

            # Check for champion in caption
            champion_name = None
            caption = table.find('caption')
            if caption:
                champion_div = caption.find('div', class_='rankings--athlete--champion')
                if champion_div:
                    champion_link = champion_div.find('h5').find('a')
                    if champion_link:
                        champion_name = champion_link.get_text(strip=True)

                        # Add champion to rankings
                        rankings_data.append({
                            'division': division_name,
                            'fighter_name': champion_name,
                            'rank': 0,
                            'is_champion': True,
                            'is_interim_champion': False,
                            'gender': self.determine_gender(division_name),
                            'ranking_type': 'P4P' if 'Pound' in division_name else 'Division'
                        })

            # Extract ranked fighters from tbody
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')

                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Get rank
                        rank_text = cells[0].get_text(strip=True)
                        try:
                            rank = int(rank_text)
                        except:
                            continue

                        # Get fighter name
                        name_link = cells[1].find('a')
                        if name_link:
                            fighter_name = name_link.get_text(strip=True)

                            # Skip if this is the champion (already added)
                            if fighter_name == champion_name:
                                continue

                            rankings_data.append({
                                'division': division_name,
                                'fighter_name': fighter_name,
                                'rank': rank,
                                'is_champion': False,
                                'is_interim_champion': False,
                                'gender': self.determine_gender(division_name),
                                'ranking_type': 'P4P' if 'Pound' in division_name else 'Division'
                            })

        return rankings_data

    def clean_division_name(self, division):
        """Clean division names"""
        # Handle specific cases
        if 'Men\'s Pound-for-Pound' in division or 'Men\'s Pound-For-Pound' in division:
            return 'Men\'s P4P'
        elif 'Women\'s Pound-for-Pound' in division or 'Women\'s Pound-For-Pound' in division:
            return 'Women\'s P4P'
        elif 'Pound-for-Pound' in division or 'Pound-For-Pound' in division:
            return 'P4P'

        # Remove extra text
        division = re.sub(r'\s*<span>.*?</span>\s*', '', division)
        division = re.sub(r'\s*Top Rank\s*', '', division)

        return division.strip()

    def determine_gender(self, division):
        """Determine gender from division"""
        return 'F' if 'Women' in division else 'M'

    def update_database(self, rankings_data):
        """Update database with scraped rankings"""
        if not rankings_data:
            print("❌ No rankings data to update")
            return False

        try:
            print(f"💾 Updating database with {len(rankings_data)} rankings...")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clear existing rankings
            cursor.execute("DELETE FROM ufc_rankings")

            # Insert new rankings
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

            conn.commit()
            conn.close()

            print("✅ Database updated successfully!")
            return True

        except Exception as e:
            print(f"❌ Database error: {e}")
            return False

    def run_scraper(self):
        """Main method to run the scraper"""
        print("🚀 Starting Accurate UFC Rankings Scraper")
        print("=" * 50)

        # Fetch page
        soup = self.fetch_rankings_page()
        if not soup:
            return False

        # Extract rankings
        rankings_data = self.extract_rankings_data(soup)
        if not rankings_data:
            print("❌ No rankings data extracted")
            return False

        # Display summary
        divisions = {}
        champions = 0

        for ranking in rankings_data:
            div = ranking['division']
            if div not in divisions:
                divisions[div] = []
            divisions[div].append(ranking)

            if ranking['is_champion']:
                champions += 1

        print(f"\n📊 EXTRACTED DATA SUMMARY:")
        print("-" * 30)
        print(f"Total fighters: {len(rankings_data)}")
        print(f"Champions: {champions}")
        print(f"Divisions: {len(divisions)}")

        for div, fighters in divisions.items():
            div_champions = sum(1 for f in fighters if f['is_champion'])
            print(f"  {div}: {len(fighters)} fighters ({div_champions} champions)")

        # Update database
        success = self.update_database(rankings_data)

        print("=" * 50)
        print(f"🏁 Scraper {'completed successfully' if success else 'completed with errors'}")

        return success

def main():
    """Main function"""
    db_path = "data/mma.db"

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Run from project root directory")
        sys.exit(1)

    scraper = AccurateUFCRankingsScraper(db_path)
    success = scraper.run_scraper()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()