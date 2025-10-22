#!/usr/bin/env python3
"""
Live UFC Rankings Scraper

Based on analysis of UFC.com/rankings, this scraper extracts real-time rankings
using the actual page structure and CSS classes discovered.

Key findings from analysis:
- 208 fighter profile links with /athlete/ URLs
- CSS classes: athlete-rankings--rank-*, athlete-rankings--attribute
- 13 champion elements, 16 ranking elements
- Division headers for all weight classes
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

class LiveUFCRankingsScraper:
    def __init__(self, db_path="data/mma.db"):
        self.db_path = db_path
        self.base_url = "https://www.ufc.com/rankings"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

        # Division mapping for consistency
        self.division_mapping = {
            "Men's Pound-For-Pound Top Rank": "Men's P4P",
            "Women's Pound-For-Pound Top Rank": "Women's P4P",
            "Pound-For-Pound Top Rank": "P4P"
        }

    def fetch_rankings_page(self):
        """Fetch the UFC rankings page"""
        try:
            print("🌐 Fetching live UFC rankings...")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"✅ Successfully fetched page ({len(response.text)} chars)")
            return soup

        except requests.RequestException as e:
            print(f"❌ Error fetching page: {e}")
            return None

    def extract_rankings_data(self, soup):
        """Extract rankings using discovered structure"""
        rankings_data = []

        try:
            # Method 1: Extract from athlete ranking tables
            tables = soup.find_all('table')
            print(f"🔍 Found {len(tables)} tables to analyze")

            for table_idx, table in enumerate(tables):
                division_data = self.extract_from_table(table, table_idx)
                rankings_data.extend(division_data)

            # Method 2: Extract from ranking sections with CSS classes
            ranking_sections = soup.find_all(['div'],
                                           class_=re.compile(r'athlete-rankings|ranking', re.I))
            print(f"🔍 Found {len(ranking_sections)} ranking sections")

            for section in ranking_sections:
                section_data = self.extract_from_section(section)
                rankings_data.extend(section_data)

            # Method 3: Extract from athlete profile links
            fighter_links = soup.find_all('a', href=re.compile(r'/athlete/'))
            print(f"🔍 Found {len(fighter_links)} fighter profile links")

            grouped_fighters = self.group_fighters_by_division(soup, fighter_links)
            rankings_data.extend(grouped_fighters)

            # Remove duplicates
            unique_rankings = self.deduplicate_rankings(rankings_data)
            print(f"📊 Extracted {len(unique_rankings)} unique rankings")

            return unique_rankings

        except Exception as e:
            print(f"❌ Error extracting rankings: {e}")
            return []

    def extract_from_table(self, table, table_idx):
        """Extract rankings from a table structure"""
        rankings = []

        try:
            # Look for table header to identify division
            division = None

            # Check for division header near the table
            prev_headers = table.find_previous(['h1', 'h2', 'h3', 'h4'])
            if prev_headers:
                header_text = prev_headers.get_text().strip()
                if any(weight in header_text for weight in ['weight', 'Pound', 'P4P']):
                    division = self.clean_division_name(header_text)

            if not division:
                division = f"Unknown Division {table_idx + 1}"

            # Extract rows
            rows = table.find_all('tr')

            for row_idx, row in enumerate(rows[1:]):  # Skip header row
                cells = row.find_all(['td', 'th'])

                if len(cells) >= 2:  # At least rank and name
                    # Try to extract rank and fighter name
                    rank_cell = cells[0].get_text().strip()
                    name_cell = cells[1].get_text().strip()

                    # Clean rank (remove #, etc.)
                    rank_match = re.search(r'(\\d+)', rank_cell)
                    if rank_match:
                        rank = int(rank_match.group(1))
                    else:
                        rank = row_idx + 1  # Use row position

                    # Clean fighter name
                    fighter_name = self.clean_fighter_name(name_cell)

                    if fighter_name and len(fighter_name.split()) >= 2:
                        # Check for champion indicators
                        is_champion = self.is_champion(row, rank_cell, name_cell)

                        rankings.append({
                            'division': division,
                            'fighter_name': fighter_name,
                            'rank': 0 if is_champion else rank,
                            'is_champion': is_champion,
                            'is_interim_champion': 'interim' in name_cell.lower(),
                            'gender': self.determine_gender(division),
                            'ranking_type': 'P4P' if 'P4P' in division or 'Pound' in division else 'Division'
                        })

        except Exception as e:
            print(f"⚠️ Error processing table {table_idx}: {e}")

        return rankings

    def extract_from_section(self, section):
        """Extract rankings from section with ranking CSS classes"""
        rankings = []

        try:
            # Look for division context
            division_header = section.find_previous(['h1', 'h2', 'h3'])
            division = "Unknown Division"

            if division_header:
                division = self.clean_division_name(division_header.get_text().strip())

            # Look for individual fighter entries
            fighter_elements = section.find_all(['div', 'li'],
                                              class_=re.compile(r'athlete|fighter', re.I))

            for fighter_elem in fighter_elements:
                fighter_data = self.extract_fighter_from_element(fighter_elem, division)
                if fighter_data:
                    rankings.append(fighter_data)

        except Exception as e:
            print(f"⚠️ Error processing section: {e}")

        return rankings

    def group_fighters_by_division(self, soup, fighter_links):
        """Group fighter links by their division context"""
        rankings = []
        current_division = "Unknown"

        try:
            for link in fighter_links:
                fighter_name = self.clean_fighter_name(link.get_text().strip())

                if not fighter_name or len(fighter_name.split()) < 2:
                    continue

                # Find division context by looking at surrounding elements
                division_context = self.find_division_context(link)
                if division_context:
                    current_division = division_context

                # Try to find rank context
                rank_context = self.find_rank_context(link)

                # Determine if champion
                is_champion = self.is_champion_from_context(link)

                rankings.append({
                    'division': current_division,
                    'fighter_name': fighter_name,
                    'rank': 0 if is_champion else (rank_context or 999),
                    'is_champion': is_champion,
                    'is_interim_champion': False,
                    'gender': self.determine_gender(current_division),
                    'ranking_type': 'P4P' if 'P4P' in current_division or 'Pound' in current_division else 'Division'
                })

        except Exception as e:
            print(f"⚠️ Error grouping fighters: {e}")

        return rankings

    def find_division_context(self, element):
        """Find division context for an element"""
        # Look for division headers before this element
        for header in element.find_all_previous(['h1', 'h2', 'h3', 'h4']):
            header_text = header.get_text().strip()
            if any(weight in header_text for weight in
                  ['Heavyweight', 'Lightweight', 'Middleweight', 'Welterweight',
                   'Featherweight', 'Bantamweight', 'Flyweight', 'Strawweight', 'Pound']):
                return self.clean_division_name(header_text)
        return None

    def find_rank_context(self, element):
        """Find rank context for an element"""
        # Look in parent elements for rank indicators
        for parent in [element.parent, element.parent.parent if element.parent else None]:
            if parent:
                text = parent.get_text()
                rank_match = re.search(r'#?(\\d+)', text)
                if rank_match:
                    return int(rank_match.group(1))
        return None

    def is_champion_from_context(self, element):
        """Check if element represents a champion"""
        # Check element and parent text for champion indicators
        for check_elem in [element, element.parent]:
            if check_elem:
                text = check_elem.get_text().lower()
                classes = ' '.join(check_elem.get('class', []))

                if any(indicator in text for indicator in ['champion', 'champ', 'title']):
                    return True
                if any(indicator in classes for indicator in ['champion', 'champ']):
                    return True
        return False

    def clean_fighter_name(self, name):
        """Clean and normalize fighter names"""
        if not name:
            return ""

        # Remove extra whitespace
        name = re.sub(r'\\s+', ' ', name.strip())

        # Remove rank numbers
        name = re.sub(r'^#?\\d+\\s*', '', name)

        # Remove common suffixes
        name = re.sub(r'\\s*\\(.*?\\)\\s*', '', name)
        name = re.sub(r'\\s*\\bC\\b\\s*$', '', name)  # Remove trailing 'C' for champion

        return name.strip()

    def clean_division_name(self, division):
        """Clean division names"""
        division = division.strip()

        # Apply mapping
        division = self.division_mapping.get(division, division)

        # Clean up common variations
        division = re.sub(r'\\s*Division\\s*', '', division)
        division = re.sub(r'\\s*Rankings?\\s*', '', division)

        return division

    def is_champion(self, row_element, rank_text, name_text):
        """Check if this represents a champion"""
        combined_text = f"{rank_text} {name_text}".lower()

        # Check for champion indicators
        champion_indicators = ['champion', 'champ', 'c ', ' c', '(c)', 'title']
        return any(indicator in combined_text for indicator in champion_indicators)

    def determine_gender(self, division):
        """Determine gender from division"""
        return 'F' if 'women' in division.lower() else 'M'

    def extract_fighter_from_element(self, element, division):
        """Extract fighter data from an individual element"""
        try:
            text = element.get_text().strip()

            # Look for fighter name pattern
            name_match = re.search(r'([A-Z][a-z]+\\s+[A-Z][a-z]+(?:\\s+[A-Z][a-z]+)?)', text)
            if not name_match:
                return None

            fighter_name = self.clean_fighter_name(name_match.group(1))

            # Look for rank
            rank_match = re.search(r'#?(\\d+)', text)
            rank = int(rank_match.group(1)) if rank_match else 999

            # Check for champion
            is_champion = self.is_champion(element, text, text)

            return {
                'division': division,
                'fighter_name': fighter_name,
                'rank': 0 if is_champion else rank,
                'is_champion': is_champion,
                'is_interim_champion': 'interim' in text.lower(),
                'gender': self.determine_gender(division),
                'ranking_type': 'P4P' if 'P4P' in division or 'Pound' in division else 'Division'
            }

        except Exception:
            return None

    def deduplicate_rankings(self, rankings_data):
        """Remove duplicate entries"""
        seen = set()
        unique_rankings = []

        for ranking in rankings_data:
            key = (ranking['division'], ranking['fighter_name'])
            if key not in seen:
                seen.add(key)
                unique_rankings.append(ranking)

        return unique_rankings

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
        print("🚀 Starting Live UFC Rankings Scraper")
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

        print(f"\\n📊 EXTRACTED DATA SUMMARY:")
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

    scraper = LiveUFCRankingsScraper(db_path)
    success = scraper.run_scraper()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()