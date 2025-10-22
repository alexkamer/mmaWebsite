#!/usr/bin/env python3
"""
UFC Rankings Update Scheduler

Provides multiple ways to keep UFC rankings current:
1. Manual update command
2. Cron job setup
3. Background scheduler (for development)

Usage:
    # Manual update
    python scripts/utilities/schedule_rankings_update.py --update

    # Generate cron job command
    python scripts/utilities/schedule_rankings_update.py --cron

    # Run background scheduler (development only)
    python scripts/utilities/schedule_rankings_update.py --background
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
import subprocess

# Add the parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class RankingsScheduler:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.join(self.script_dir, '..', '..')
        self.update_script = os.path.join(self.script_dir, 'update_rankings.py')

    def manual_update(self):
        """Run a manual rankings update"""
        print("🚀 Running manual UFC rankings update...")
        try:
            result = subprocess.run([
                sys.executable, self.update_script
            ], cwd=self.project_root, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Rankings updated successfully!")
                if result.stdout:
                    print(result.stdout)
            else:
                print("❌ Rankings update failed!")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error running update: {e}")
            return False

        return True

    def generate_cron_setup(self):
        """Generate cron job setup instructions"""
        python_path = sys.executable
        script_path = os.path.abspath(self.update_script)
        project_path = os.path.abspath(self.project_root)

        print("📋 UFC Rankings Cron Job Setup")
        print("=" * 50)
        print()
        print("To automatically update UFC rankings, add this cron job:")
        print()
        print("1. Open your crontab:")
        print("   crontab -e")
        print()
        print("2. Add this line to update rankings daily at 6 AM:")
        print(f"   0 6 * * * cd {project_path} && {python_path} {script_path} >> /tmp/ufc_rankings.log 2>&1")
        print()
        print("3. Alternative schedules:")
        print("   # Every 12 hours (6 AM and 6 PM):")
        print(f"   0 6,18 * * * cd {project_path} && {python_path} {script_path}")
        print()
        print("   # Weekly on Sundays at 8 AM (after typical UFC events):")
        print(f"   0 8 * * 0 cd {project_path} && {python_path} {script_path}")
        print()
        print("   # After every UFC event (manually trigger when needed):")
        print(f"   # {python_path} {script_path}")
        print()
        print("4. Check cron status:")
        print("   crontab -l")
        print("   tail -f /tmp/ufc_rankings.log")
        print()
        print("=" * 50)

    def background_scheduler(self, update_interval_hours=24):
        """Run a background scheduler (for development)"""
        print(f"🔄 Starting background scheduler (updates every {update_interval_hours} hours)")
        print("Press Ctrl+C to stop")
        print("=" * 50)

        next_update = datetime.now()

        try:
            while True:
                current_time = datetime.now()

                if current_time >= next_update:
                    print(f"\\n⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Running scheduled update...")

                    success = self.manual_update()

                    if success:
                        next_update = current_time + timedelta(hours=update_interval_hours)
                        print(f"✅ Next update scheduled for: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        # Retry in 1 hour if failed
                        next_update = current_time + timedelta(hours=1)
                        print(f"⚠️ Update failed. Retrying in 1 hour: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")

                # Check every minute
                time.sleep(60)

        except KeyboardInterrupt:
            print("\\n🛑 Background scheduler stopped by user")
        except Exception as e:
            print(f"\\n❌ Background scheduler error: {e}")

    def check_update_needed(self):
        """Check if rankings need updating based on last update time"""
        try:
            import sqlite3
            db_path = os.path.join(self.project_root, "data", "mma.db")

            if not os.path.exists(db_path):
                print("❌ Database not found - update needed")
                return True

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get last update time
            result = cursor.execute("""
                SELECT MAX(last_updated) FROM ufc_rankings
            """).fetchone()

            conn.close()

            if not result[0]:
                print("❌ No rankings found - update needed")
                return True

            # Check if last update was more than 24 hours ago
            last_update = datetime.fromisoformat(result[0].replace('Z', '+00:00') if 'Z' in result[0] else result[0])
            hours_since_update = (datetime.now() - last_update.replace(tzinfo=None)).total_seconds() / 3600

            if hours_since_update > 24:
                print(f"⏰ Rankings are {hours_since_update:.1f} hours old - update recommended")
                return True
            else:
                print(f"✅ Rankings are current ({hours_since_update:.1f} hours old)")
                return False

        except Exception as e:
            print(f"⚠️ Error checking update status: {e}")
            return True

def main():
    parser = argparse.ArgumentParser(description="UFC Rankings Update Scheduler")
    parser.add_argument('--update', action='store_true', help='Run manual rankings update')
    parser.add_argument('--cron', action='store_true', help='Show cron job setup instructions')
    parser.add_argument('--background', action='store_true', help='Run background scheduler (development)')
    parser.add_argument('--check', action='store_true', help='Check if update is needed')
    parser.add_argument('--interval', type=int, default=24, help='Update interval in hours (for background mode)')

    args = parser.parse_args()

    scheduler = RankingsScheduler()

    if args.update:
        success = scheduler.manual_update()
        sys.exit(0 if success else 1)

    elif args.cron:
        scheduler.generate_cron_setup()

    elif args.background:
        scheduler.background_scheduler(args.interval)

    elif args.check:
        needs_update = scheduler.check_update_needed()
        sys.exit(1 if needs_update else 0)

    else:
        # Default: show help and current status
        parser.print_help()
        print("\\n" + "=" * 50)
        print("📊 Current Rankings Status:")
        scheduler.check_update_needed()

if __name__ == "__main__":
    main()