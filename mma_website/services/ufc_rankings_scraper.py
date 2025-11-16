"""
Scraper for UFC official rankings from ufc.com
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import httpx
from sqlalchemy import text
from mma_website import db

logger = logging.getLogger(__name__)


class UFCRankingsScraper:
    """Scrapes current UFC rankings from UFC.com"""

    UFC_RANKINGS_URL = "https://www.ufc.com/rankings"
    TIMEOUT = 30

    # Division name normalization
    DIVISION_MAP = {
        'pound-for-pound': 'Pound for Pound',
        "women's pound-for-pound": "Women's Pound for Pound",
        'heavyweight': 'Heavyweight',
        'light heavyweight': 'Light Heavyweight',
        'middleweight': 'Middleweight',
        'welterweight': 'Welterweight',
        'lightweight': 'Lightweight',
        'featherweight': 'Featherweight',
        'bantamweight': 'Bantamweight',
        'flyweight': 'Flyweight',
        "women's bantamweight": "Women's Bantamweight",
        "women's flyweight": "Women's Flyweight",
        "women's strawweight": "Women's Strawweight",
    }

    def __init__(self):
        self.client = httpx.Client(
            timeout=self.TIMEOUT,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            follow_redirects=True
        )
        self.update_stats = {
            'total_divisions': 0,
            'updated_rankings': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def scrape_rankings(self) -> List[Dict]:
        """
        Scrape rankings from UFC.com

        Returns:
            List of ranking dictionaries
        """
        logger.info("Scraping UFC rankings from ufc.com")

        try:
            response = self.client.get(self.UFC_RANKINGS_URL)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            rankings = []

            # Find all ranking tables
            # UFC website structure: look for ranking sections
            ranking_sections = soup.find_all(['div', 'section'], class_=lambda x: x and ('ranking' in x.lower() or 'fighter' in x.lower()))

            if not ranking_sections:
                logger.warning("Could not find ranking sections, trying alternative selectors")
                # Try to find tables or structured data
                ranking_sections = soup.find_all('table')

            logger.info(f"Found {len(ranking_sections)} potential ranking sections")

            # Parse each section
            for section in ranking_sections:
                division_data = self._parse_ranking_section(section)
                if division_data:
                    rankings.append(division_data)

            logger.info(f"Successfully scraped {len(rankings)} divisions")
            return rankings

        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping UFC rankings: {e}")
            self.update_stats['errors'] += 1
            return []
        except Exception as e:
            logger.error(f"Error scraping UFC rankings: {e}", exc_info=True)
            self.update_stats['errors'] += 1
            return []

    def _parse_ranking_section(self, section) -> Optional[Dict]:
        """Parse a single ranking section"""
        try:
            # Try to find division name
            division_elem = section.find(['h2', 'h3', 'h4', 'span'], class_=lambda x: x and 'division' in x.lower())
            if not division_elem:
                division_elem = section.find(['h2', 'h3', 'h4'])

            if not division_elem:
                return None

            division_name = division_elem.get_text(strip=True)
            division_name = self.DIVISION_MAP.get(division_name.lower(), division_name)

            # Find fighters in this section
            fighters = []
            fighter_elements = section.find_all(['tr', 'div', 'li'], class_=lambda x: x and ('fighter' in x.lower() or 'athlete' in x.lower()))

            for idx, fighter_elem in enumerate(fighter_elements[:15], 1):  # Top 15
                fighter_name = self._extract_fighter_name(fighter_elem)
                if fighter_name:
                    fighters.append({
                        'rank': idx,
                        'name': fighter_name,
                        'is_champion': idx == 1  # First is usually champion
                    })

            if fighters:
                return {
                    'division': division_name,
                    'fighters': fighters,
                    'ranking_type': 'Pound for Pound' if 'pound' in division_name.lower() else 'Division'
                }

            return None

        except Exception as e:
            logger.debug(f"Error parsing ranking section: {e}")
            return None

    def _extract_fighter_name(self, element) -> Optional[str]:
        """Extract fighter name from element"""
        try:
            # Try various selectors
            name_elem = element.find(['span', 'a', 'div'], class_=lambda x: x and 'name' in x.lower())
            if name_elem:
                return name_elem.get_text(strip=True)

            # Try direct text
            text = element.get_text(strip=True)
            if text and len(text) < 50:  # Reasonable name length
                return text

            return None
        except:
            return None

    def update_rankings(self) -> Dict:
        """
        Update all UFC rankings in database

        Returns:
            Dict with update statistics
        """
        self.update_stats['start_time'] = datetime.now()
        logger.info("Starting UFC rankings update from ufc.com")

        try:
            # Scrape rankings
            rankings = self.scrape_rankings()
            self.update_stats['total_divisions'] = len(rankings)

            if not rankings:
                logger.error("No rankings scraped from UFC.com")
                self.update_stats['errors'] += 1
                return self.update_stats

            # Process each division
            for division_data in rankings:
                self._update_division_rankings(division_data)

            # Commit changes
            db.session.commit()
            logger.info("Rankings update completed successfully")

        except Exception as e:
            logger.error(f"Error during rankings update: {e}", exc_info=True)
            db.session.rollback()
            self.update_stats['errors'] += 1

        self.update_stats['end_time'] = datetime.now()
        duration = (self.update_stats['end_time'] - self.update_stats['start_time']).total_seconds()

        logger.info(f"Rankings update complete: {self.update_stats['updated_rankings']} rankings updated "
                   f"in {duration:.2f}s")

        return self.update_stats

    def _update_division_rankings(self, division_data: Dict) -> None:
        """Update rankings for a single division"""
        division = division_data['division']
        ranking_type = division_data['ranking_type']
        fighters = division_data['fighters']

        logger.info(f"Updating rankings for {division} ({len(fighters)} fighters)")

        # Delete old rankings for this division
        db.session.execute(text("""
            DELETE FROM ufc_rankings
            WHERE division = :division AND ranking_type = :ranking_type
        """), {"division": division, "ranking_type": ranking_type})

        # Insert new rankings
        for fighter in fighters:
            try:
                # Try to find athlete ID from our database
                result = db.session.execute(text("""
                    SELECT id FROM athletes
                    WHERE LOWER(full_name) = LOWER(:name)
                    LIMIT 1
                """), {"name": fighter['name']}).fetchone()

                athlete_id = result[0] if result else None

                db.session.execute(text("""
                    INSERT INTO ufc_rankings
                    (division, fighter_name, rank, is_champion, is_interim_champion, ranking_type, athlete_id, last_updated)
                    VALUES (:division, :fighter_name, :rank, :is_champion, :is_interim, :ranking_type, :athlete_id, :updated)
                """), {
                    "division": division,
                    "fighter_name": fighter['name'],
                    "rank": fighter['rank'],
                    "is_champion": 1 if fighter['is_champion'] else 0,
                    "is_interim": 0,
                    "ranking_type": ranking_type,
                    "athlete_id": str(athlete_id) if athlete_id else None,
                    "updated": datetime.now().isoformat()
                })

                self.update_stats['updated_rankings'] += 1

            except Exception as e:
                logger.error(f"Error updating fighter {fighter['name']}: {e}")
                self.update_stats['errors'] += 1

    def close(self):
        """Close HTTP client"""
        self.client.close()


# Singleton instance
_ufc_scraper = None


def get_ufc_scraper() -> UFCRankingsScraper:
    """Get or create UFC scraper singleton"""
    global _ufc_scraper
    if _ufc_scraper is None:
        _ufc_scraper = UFCRankingsScraper()
    return _ufc_scraper
