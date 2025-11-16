"""
Data Update Tasks
Background jobs for keeping MMA database fresh and current
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def run_incremental_update():
    """
    Run incremental update (checks last 90 days + upcoming events)
    Faster than full update, suitable for daily runs
    """
    logger.info("Starting incremental update job")

    try:
        from scripts.incremental_update import IncrementalUpdater

        updater = IncrementalUpdater(lookback_days=90)
        updater.run()

        logger.info(f"Incremental update completed successfully: "
                   f"{updater.stats['fights_added']} fights added, "
                   f"{updater.stats['cards_added']} cards added")

        # Update last run timestamp
        _update_last_run_timestamp('incremental_update')

        return {
            'success': True,
            'stats': updater.stats,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in incremental update job: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def run_post_event_update():
    """
    Run after major events (Sundays after UFC events)
    More thorough check for recent fight results and statistics
    """
    logger.info("Starting post-event update job")

    try:
        from scripts.incremental_update import IncrementalUpdater

        # Check last 30 days more thoroughly after events
        updater = IncrementalUpdater(lookback_days=30)
        updater.run()

        logger.info(f"Post-event update completed: "
                   f"{updater.stats['fights_added']} fights updated")

        _update_last_run_timestamp('post_event_update')

        return {
            'success': True,
            'stats': updater.stats,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in post-event update job: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def run_rankings_update():
    """
    Update UFC rankings (typically updated on Tuesdays)
    """
    logger.info("Starting rankings update job")

    try:
        from mma_website.services.rankings_update_service import get_rankings_service
        from mma_website import db

        with db.session.begin():
            service = get_rankings_service()
            stats = service.update_rankings()

            logger.info(f"Rankings update completed: "
                       f"{stats['updated_rankings']} rankings updated, "
                       f"{stats['errors']} errors")

            _update_last_run_timestamp('rankings_update')

            return {
                'success': True,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Error in rankings update job: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def run_odds_update():
    """
    Update betting odds for upcoming fights
    Runs every 6 hours to keep odds current
    """
    logger.info("Starting odds update job")

    try:
        import sqlite3

        # Get upcoming fights (next 30 days) with odds URLs
        conn = sqlite3.connect('data/mma.db')
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT f.odds_url
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        WHERE c.date >= date('now')
        AND c.date <= date('now', '+30 days')
        AND f.odds_url IS NOT NULL
        AND f.odds_url != ''
        """

        odds_urls = [row[0] for row in cursor.execute(query).fetchall()]
        conn.close()

        if odds_urls:
            logger.info(f"Found {len(odds_urls)} fights with odds to update")
            # For now, just check and log (odds scraping can be enhanced later)
            logger.info("Odds update check completed")

            _update_last_run_timestamp('odds_update')

            return {
                'success': True,
                'odds_checked': len(odds_urls),
                'timestamp': datetime.now().isoformat()
            }
        else:
            logger.info("No upcoming fights with odds found")
            _update_last_run_timestamp('odds_update')

            return {
                'success': True,
                'odds_checked': 0,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Error in odds update job: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def _update_last_run_timestamp(job_name: str):
    """
    Update last run timestamp for a job in database
    Creates a simple metadata table to track update times
    """
    try:
        import sqlite3
        from datetime import datetime

        conn = sqlite3.connect('data/mma.db')
        cursor = conn.cursor()

        # Create metadata table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS update_metadata (
                job_name TEXT PRIMARY KEY,
                last_run TIMESTAMP,
                last_status TEXT,
                last_error TEXT
            )
        """)

        # Insert or update timestamp
        cursor.execute("""
            INSERT OR REPLACE INTO update_metadata (job_name, last_run, last_status)
            VALUES (?, ?, ?)
        """, (job_name, datetime.now(), 'success'))

        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"Error updating timestamp for {job_name}: {e}")


def get_last_update_times():
    """Get last update times for all jobs"""
    try:
        import sqlite3

        conn = sqlite3.connect('data/mma.db')
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='update_metadata'
        """)

        if not cursor.fetchone():
            conn.close()
            return {}

        cursor.execute("SELECT job_name, last_run, last_status FROM update_metadata")
        results = {row[0]: {'last_run': row[1], 'status': row[2]}
                  for row in cursor.fetchall()}

        conn.close()
        return results

    except Exception as e:
        logger.error(f"Error getting last update times: {e}")
        return {}
