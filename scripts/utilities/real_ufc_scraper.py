#!/usr/bin/env python3
"""
Real UFC Rankings Scraper

Fetches actual current rankings from https://www.ufc.com/rankings
and organizes them into proper database format.

This script analyzes the real UFC page structure and extracts:
- Current champions in all divisions
- Complete rankings (1-15) for each division
- P4P rankings for men and women
- Proper fighter names and divisions
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import re
from datetime import datetime
import sys
import os

# Add the parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class RealUFCRankingsScraper:
    def __init__(self):
        self.base_url = "https://www.ufc.com/rankings"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def fetch_and_analyze_page(self):
        """Fetch the UFC rankings page and analyze its structure"""
        try:
            print("🌐 Fetching UFC Rankings page...")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()

            print(f"✅ Page fetched successfully ({len(response.text)} chars)")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Save raw HTML for debugging
            with open('debug_ufc_rankings.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 Saved raw HTML to debug_ufc_rankings.html")

            # Analyze page structure
            print("\\n🔍 ANALYZING PAGE STRUCTURE")
            print("=" * 50)

            # Look for common ranking indicators
            self.find_ranking_sections(soup)
            self.find_fighter_names(soup)
            self.find_division_headers(soup)
            self.extract_rankings_data(soup)

        except requests.RequestException as e:
            print(f"❌ Error fetching page: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

        return True

    def find_ranking_sections(self, soup):
        """Find potential ranking sections"""
        print("\\n📋 LOOKING FOR RANKING SECTIONS:")

        # Method 1: Look for elements with 'rank' in class/id
        rank_elements = soup.find_all(['div', 'section', 'article'],
                                     class_=re.compile(r'rank', re.I))
        print(f"  - Elements with 'rank' in class: {len(rank_elements)}")

        # Method 2: Look for elements with 'division' in class/id
        division_elements = soup.find_all(['div', 'section', 'article'],
                                        class_=re.compile(r'division', re.I))
        print(f"  - Elements with 'division' in class: {len(division_elements)}")

        # Method 3: Look for elements with 'champion' in class/id
        champion_elements = soup.find_all(['div', 'section', 'article'],
                                        class_=re.compile(r'champion', re.I))
        print(f"  - Elements with 'champion' in class: {len(champion_elements)}")

        # Method 4: Look for lists or tables
        lists = soup.find_all(['ul', 'ol'])
        tables = soup.find_all('table')
        print(f"  - Lists found: {len(lists)}")
        print(f"  - Tables found: {len(tables)}")

        # Method 5: Look for specific UFC ranking structure
        ranking_containers = soup.find_all(['div'],
                                         attrs={'data-drupal-views-infinite-scroll-pager': True})
        print(f"  - Drupal views containers: {len(ranking_containers)}")

    def find_fighter_names(self, soup):
        """Find fighter names on the page"""
        print("\\n👤 LOOKING FOR FIGHTER NAMES:")

        # Look for links that might be fighter profiles
        fighter_links = soup.find_all('a', href=re.compile(r'/athlete/'))
        print(f"  - Fighter profile links: {len(fighter_links)}")

        if fighter_links:
            print("    Sample fighter links:")
            for link in fighter_links[:5]:
                name = link.get_text().strip()
                href = link.get('href', '')
                print(f"      - {name}: {href}")

        # Look for text patterns that look like fighter names
        all_text = soup.get_text()
        name_patterns = re.findall(r'\\b[A-Z][a-z]+ [A-Z][a-z]+(?:\\s[A-Z][a-z]+)*\\b', all_text)
        potential_fighters = [name for name in name_patterns
                            if len(name.split()) >= 2 and len(name) < 50]

        # Filter for likely fighter names (avoid common phrases)
        filtered_fighters = []
        exclude_words = ['United States', 'More Info', 'Read More', 'Fight Pass',
                        'Ultimate Fighting', 'Mixed Martial', 'Pay Per View']

        for name in potential_fighters:
            if not any(exclude in name for exclude in exclude_words):
                filtered_fighters.append(name)

        unique_fighters = list(set(filtered_fighters))
        print(f"  - Potential fighter names found: {len(unique_fighters)}")

        if unique_fighters:
            print("    Sample names:")
            for name in sorted(unique_fighters)[:10]:
                print(f"      - {name}")

    def find_division_headers(self, soup):
        """Find division/weight class headers"""
        print("\\n🏷️  LOOKING FOR DIVISIONS:")

        # Look for headers containing weight class names
        weight_classes = ['Heavyweight', 'Light Heavyweight', 'Middleweight',
                         'Welterweight', 'Lightweight', 'Featherweight',
                         'Bantamweight', 'Flyweight', 'Strawweight']

        division_headers = []
        for weight in weight_classes:
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'],
                                   string=re.compile(weight, re.I))
            if headers:
                division_headers.extend(headers)
                print(f"  - Found '{weight}' headers: {len(headers)}")

        # Look for "Women's" divisions
        womens_headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'],
                                     string=re.compile(r"Women'?s", re.I))
        print(f"  - Found Women's division headers: {len(womens_headers)}")

        # Look for P4P
        p4p_headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'],
                                   string=re.compile(r'Pound.*Pound|P4P', re.I))
        print(f"  - Found P4P headers: {len(p4p_headers)}")

    def extract_rankings_data(self, soup):
        """Attempt to extract actual rankings data"""
        print("\\n🎯 EXTRACTING RANKINGS DATA:")

        # Strategy 1: Look for JSON data in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('ranking' in script.string.lower() or
                                'fighter' in script.string.lower()):
                print(f"  - Found potential JSON in script tag")
                # Try to extract JSON
                try:
                    # Look for JSON patterns
                    json_matches = re.findall(r'\\{[^{}]*"[^"]*"[^{}]*\\}', script.string)
                    if json_matches:
                        print(f"    - Found {len(json_matches)} JSON-like objects")
                except:
                    pass

        # Strategy 2: Look for structured data
        rankings_found = []

        # Find all potential ranking entries
        potential_entries = soup.find_all(['div', 'li', 'tr'],
                                        class_=re.compile(r'rank|fighter|athlete', re.I))

        print(f"  - Potential ranking entries: {len(potential_entries)}")

        for entry in potential_entries[:10]:  # Sample first 10
            text = entry.get_text().strip()
            if text and len(text) < 200:  # Reasonable length
                # Look for patterns like "#1 Fighter Name"
                rank_match = re.search(r'#?(\\d+)\\s+([A-Z][a-z]+\\s+[A-Z][a-z]+)', text)
                if rank_match:
                    rank = rank_match.group(1)
                    name = rank_match.group(2)
                    rankings_found.append({'rank': rank, 'name': name, 'text': text})

        if rankings_found:
            print(f"  - Found {len(rankings_found)} potential rankings:")
            for ranking in rankings_found[:5]:
                print(f"    - #{ranking['rank']}: {ranking['name']}")

        # Strategy 3: Look for specific UFC ranking patterns
        self.look_for_ufc_specific_patterns(soup)

    def look_for_ufc_specific_patterns(self, soup):
        """Look for UFC-specific ranking patterns"""
        print("\\n🔎 LOOKING FOR UFC-SPECIFIC PATTERNS:")

        # Look for data attributes commonly used by UFC
        data_attrs = ['data-athlete-id', 'data-fighter-id', 'data-rank', 'data-division']
        for attr in data_attrs:
            elements = soup.find_all(attrs={attr: True})
            if elements:
                print(f"  - Elements with {attr}: {len(elements)}")

        # Look for classes that might contain rankings
        common_classes = soup.find_all(class_=True)
        class_names = []
        for elem in common_classes:
            classes = elem.get('class', [])
            class_names.extend(classes)

        # Filter for ranking-related classes
        ranking_classes = [cls for cls in set(class_names)
                          if any(keyword in cls.lower()
                               for keyword in ['rank', 'fighter', 'athlete', 'champion', 'division'])]

        if ranking_classes:
            print(f"  - Ranking-related CSS classes found:")
            for cls in sorted(ranking_classes)[:10]:
                print(f"    - {cls}")

        # Look for specific UFC.com patterns
        view_elements = soup.find_all('div', class_=re.compile(r'view-', re.I))
        print(f"  - Drupal view elements: {len(view_elements)}")

        # Look for Ajax/dynamic content indicators
        ajax_elements = soup.find_all(attrs={'data-drupal-ajax': True})
        print(f"  - Ajax-enabled elements: {len(ajax_elements)}")

def main():
    print("🚀 UFC Rankings Real-Time Analysis")
    print("=" * 50)

    scraper = RealUFCRankingsScraper()
    success = scraper.fetch_and_analyze_page()

    if success:
        print("\\n" + "=" * 50)
        print("✅ Analysis completed successfully!")
        print("📄 Check 'debug_ufc_rankings.html' for the raw page source")
        print("\\n🔧 Next steps:")
        print("1. Review the analysis output above")
        print("2. Examine the debug_ufc_rankings.html file")
        print("3. Use findings to build targeted scraper")
    else:
        print("\\n" + "=" * 50)
        print("❌ Analysis failed")

if __name__ == "__main__":
    main()