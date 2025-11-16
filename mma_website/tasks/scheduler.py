"""
Task scheduler for automated data updates
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import os

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def update_rankings_job():
    """Job to update UFC rankings"""
    from mma_website.services.rankings_update_service import get_rankings_service
    from mma_website import db

    logger.info("Starting scheduled rankings update")

    try:
        with db.session.begin():
            service = get_rankings_service()
            stats = service.update_rankings()

            logger.info(f"Scheduled rankings update completed: "
                       f"{stats['updated_rankings']} rankings updated, "
                       f"{stats['errors']} errors")

    except Exception as e:
        logger.error(f"Error in scheduled rankings update: {e}", exc_info=True)


def incremental_update_job():
    """Job to run incremental database update"""
    from mma_website.tasks.update_tasks import run_incremental_update
    logger.info("Starting scheduled incremental update")

    try:
        result = run_incremental_update()
        if result['success']:
            logger.info(f"Scheduled incremental update completed: {result['stats']}")
        else:
            logger.error(f"Scheduled incremental update failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error in scheduled incremental update: {e}", exc_info=True)


def post_event_update_job():
    """Job to run post-event update (after UFC events)"""
    from mma_website.tasks.update_tasks import run_post_event_update
    logger.info("Starting scheduled post-event update")

    try:
        result = run_post_event_update()
        if result['success']:
            logger.info(f"Scheduled post-event update completed: {result['stats']}")
        else:
            logger.error(f"Scheduled post-event update failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error in scheduled post-event update: {e}", exc_info=True)


def odds_update_job():
    """Job to update betting odds"""
    from mma_website.tasks.update_tasks import run_odds_update
    logger.info("Starting scheduled odds update")

    try:
        result = run_odds_update()
        if result['success']:
            logger.info(f"Scheduled odds update completed: {result.get('odds_checked', 0)} odds checked")
        else:
            logger.error(f"Scheduled odds update failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error in scheduled odds update: {e}", exc_info=True)


def init_scheduler(app):
    """
    Initialize and start the task scheduler

    Args:
        app: Flask application instance
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return scheduler

    # Check if scheduler should be enabled
    if not app.config.get('SCHEDULER_ENABLED', True):
        logger.info("Scheduler disabled by configuration")
        return None

    logger.info("Initializing task scheduler")

    scheduler = BackgroundScheduler(
        daemon=True,
        timezone='America/New_York'  # UFC headquarters timezone (EST/EDT)
    )

    # Add jobs based on configuration

    # 1. Daily incremental update - 6 AM EST
    incremental_cron = os.getenv('INCREMENTAL_UPDATE_CRON', '0 6 * * *')
    try:
        scheduler.add_job(
            func=incremental_update_job,
            trigger=CronTrigger.from_crontab(incremental_cron),
            id='incremental_update',
            name='Daily Incremental Update',
            replace_existing=True,
            misfire_grace_time=3600
        )
        logger.info(f"Scheduled incremental update: {incremental_cron}")
    except Exception as e:
        logger.error(f"Error scheduling incremental update: {e}")

    # 2. Post-event update - Sundays at 2 AM EST (after Saturday UFC events)
    post_event_cron = os.getenv('POST_EVENT_UPDATE_CRON', '0 2 * * 0')
    try:
        scheduler.add_job(
            func=post_event_update_job,
            trigger=CronTrigger.from_crontab(post_event_cron),
            id='post_event_update',
            name='Post-Event Update (Sundays)',
            replace_existing=True,
            misfire_grace_time=3600
        )
        logger.info(f"Scheduled post-event update: {post_event_cron}")
    except Exception as e:
        logger.error(f"Error scheduling post-event update: {e}")

    # 3. Rankings update - Tuesdays at 3 PM EST
    rankings_cron = os.getenv('RANKINGS_UPDATE_CRON', '0 15 * * 2')
    try:
        scheduler.add_job(
            func=update_rankings_job,
            trigger=CronTrigger.from_crontab(rankings_cron),
            id='update_rankings',
            name='Update UFC Rankings (Tuesdays)',
            replace_existing=True,
            misfire_grace_time=3600
        )
        logger.info(f"Scheduled rankings update: {rankings_cron}")
    except Exception as e:
        logger.error(f"Error scheduling rankings update: {e}")

    # 4. Odds update - Every 6 hours
    try:
        scheduler.add_job(
            func=odds_update_job,
            trigger=IntervalTrigger(hours=6),
            id='odds_update',
            name='Odds Update (Every 6 Hours)',
            replace_existing=True,
            misfire_grace_time=1800
        )
        logger.info("Scheduled odds update: every 6 hours")
    except Exception as e:
        logger.error(f"Error scheduling odds update: {e}")

    # Start the scheduler
    try:
        scheduler.start()
        logger.info("Task scheduler started successfully with 4 jobs")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}", exc_info=True)

    return scheduler


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    global scheduler

    if scheduler is not None:
        logger.info("Shutting down task scheduler")
        scheduler.shutdown(wait=True)
        scheduler = None


def get_scheduler():
    """Get the current scheduler instance"""
    return scheduler


def get_scheduled_jobs():
    """Get list of all scheduled jobs"""
    if scheduler is None:
        return []

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })

    return jobs
