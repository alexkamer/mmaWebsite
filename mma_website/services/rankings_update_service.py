"""
Service for updating UFC rankings from UFC.com official website
"""
import httpx
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import text
from bs4 import BeautifulSoup
from mma_website import db
from mma_website.utils.logger import PerformanceLogger

logger = logging.getLogger(__name__)


class RankingsUpdateService:
    """Service for fetching and updating UFC rankings from UFC.com"""

    UFC_RANKINGS_URL = "https://www.ufc.com/rankings"
    TIMEOUT = 30

    def __init__(self):
        self.client = httpx.Client(
            timeout=self.TIMEOUT,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
            follow_redirects=True
        )
        self.update_stats = {
            'total_divisions': 0,
            'updated_rankings': 0,
            'new_fighters': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def fetch_all_rankings(self) -> List[Dict]:
        """Fetch all UFC rankings from UFC.com"""
        logger.info("Fetching UFC rankings from UFC.com")

        try:
            response = self.client.get(self.UFC_RANKINGS_URL)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            rankings = []

            # Find all ranking groups
            ranking_groups = soup.find_all('div', class_='view-grouping')

            for group in ranking_groups:
                ranking_data = self._parse_ranking_group(group)
                if ranking_data and ranking_data.get('fighters'):
                    rankings.append(ranking_data)

            logger.info(f"Fetched {len(rankings)} division rankings")
            return rankings

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching rankings: {e}")
            self.update_stats['errors'] += 1
            return []
        except Exception as e:
            logger.error(f"Error fetching rankings: {e}", exc_info=True)
            self.update_stats['errors'] += 1
            return []

    def _parse_ranking_group(self, group) -> Optional[Dict]:
        """Parse a single ranking group from UFC.com"""
        try:
            # Get division name from header
            header = group.find('div', class_='view-grouping-header')
            if not header:
                return None

            division_text = header.get_text(strip=True)
            # Clean up division name (remove "Top Rank" suffix)
            division_name = division_text.replace('Top Rank', '').strip()

            # Determine ranking type
            ranking_type = 'Pound for Pound' if 'Pound-for-Pound' in division_name else 'Division'

            fighters = []

            # Get champion from caption
            caption = group.find('caption')
            if caption:
                champion_div = caption.find('div', class_='rankings--athlete--champion')
                if champion_div:
                    h5 = champion_div.find('h5')
                    if h5:
                        link = h5.find('a')
                        if link:
                            champion_name = link.get_text(strip=True)
                            fighters.append({
                                'rank': 1,
                                'name': champion_name,
                                'is_champion': True
                            })

            # Get ranked fighters from tbody
            tbody = group.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    rank_td = row.find('td', class_='views-field-weight-class-rank')
                    name_td = row.find('td', class_='views-field-title')

                    if rank_td and name_td:
                        try:
                            rank = int(rank_td.get_text(strip=True))
                            name_link = name_td.find('a')
                            if name_link:
                                fighter_name = name_link.get_text(strip=True)
                                fighters.append({
                                    'rank': rank,
                                    'name': fighter_name,
                                    'is_champion': False
                                })
                        except ValueError:
                            continue

            if fighters:
                return {
                    'division': division_name,
                    'fighters': fighters,
                    'ranking_type': ranking_type
                }

            return None

        except Exception as e:
            logger.debug(f"Error parsing ranking group: {e}")
            return None

    def update_rankings(self) -> Dict:
        """
        Update all UFC rankings in the database

        Returns:
            Dict with update statistics
        """
        self.update_stats['start_time'] = datetime.now()
        logger.info("Starting UFC rankings update from UFC.com")

        with PerformanceLogger(logger, "rankings_update"):
            try:
                # Fetch all current rankings from UFC.com
                rankings = self.fetch_all_rankings()
                self.update_stats['total_divisions'] = len(rankings)

                # Process each division
                for ranking_data in rankings:
                    self._process_division_ranking(ranking_data)

                # Commit all changes
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

    def _process_division_ranking(self, ranking_data: Dict) -> None:
        """Process and save rankings for a single division"""
        division_name = ranking_data.get('division', '')
        ranking_type = ranking_data.get('ranking_type', 'Division')
        fighters = ranking_data.get('fighters', [])

        logger.info(f"Processing rankings for {division_name} ({len(fighters)} fighters)")

        # Save current rankings to history before deleting
        db.session.execute(text("""
            INSERT OR IGNORE INTO ufc_rankings_history
                (division, fighter_name, rank, is_champion, is_interim_champion, ranking_type, athlete_id, snapshot_date)
            SELECT division, fighter_name, rank, is_champion, is_interim_champion, ranking_type, athlete_id, last_updated
            FROM ufc_rankings
            WHERE division = :division AND ranking_type = :ranking_type
        """), {"division": division_name, "ranking_type": ranking_type})

        # Delete existing rankings for this division
        db.session.execute(text("""
            DELETE FROM ufc_rankings
            WHERE division = :division AND ranking_type = :ranking_type
        """), {"division": division_name, "ranking_type": ranking_type})

        # Process each ranked fighter
        for fighter in fighters:
            self._process_fighter_ranking(fighter, division_name, ranking_type)

    def _process_fighter_ranking(self, fighter: Dict, division: str, ranking_type: str) -> None:
        """Process a single fighter ranking and insert into database"""
        try:
            rank = fighter.get('rank', 0)
            fighter_name = fighter.get('name', '')
            is_champion = fighter.get('is_champion', False)

            if not fighter_name:
                return

            # Try to get athlete ID from our database
            result = db.session.execute(text("""
                SELECT id FROM athletes
                WHERE LOWER(full_name) = LOWER(:name)
                LIMIT 1
            """), {"name": fighter_name}).fetchone()

            athlete_id = str(result[0]) if result else None

            # Insert ranking
            db.session.execute(text("""
                INSERT INTO ufc_rankings
                (division, fighter_name, rank, is_champion, is_interim_champion, ranking_type, athlete_id, last_updated)
                VALUES (:division, :fighter_name, :rank, :is_champion, :is_interim, :ranking_type, :athlete_id, :updated)
            """), {
                "division": division,
                "fighter_name": fighter_name,
                "rank": rank,
                "is_champion": 1 if is_champion else 0,
                "is_interim": 0,
                "ranking_type": ranking_type,
                "athlete_id": athlete_id,
                "updated": datetime.now().isoformat()
            })

            self.update_stats['updated_rankings'] += 1

        except Exception as e:
            logger.error(f"Error processing fighter {fighter.get('name')}: {e}", exc_info=True)
            self.update_stats['errors'] += 1

    def get_last_update_time(self) -> Optional[datetime]:
        """Get the timestamp of the last rankings update"""
        try:
            result = db.session.execute(text("""
                SELECT MAX(last_updated) as last_update FROM ufc_rankings
            """)).fetchone()

            if result and result[0]:
                return datetime.fromisoformat(result[0])
            return None
        except Exception as e:
            logger.error(f"Error getting last update time: {e}")
            return None

    def needs_update(self, hours: int = 24) -> bool:
        """
        Check if rankings need to be updated

        Args:
            hours: Number of hours since last update to trigger update

        Returns:
            True if update is needed
        """
        last_update = self.get_last_update_time()

        if not last_update:
            return True

        hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
        return hours_since_update >= hours

    def close(self):
        """Close HTTP client"""
        self.client.close()


# Singleton instance
_rankings_service = None


def get_rankings_service() -> RankingsUpdateService:
    """Get or create rankings update service singleton"""
    global _rankings_service
    if _rankings_service is None:
        _rankings_service = RankingsUpdateService()
    return _rankings_service
