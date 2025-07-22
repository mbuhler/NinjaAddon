from apscheduler.schedulers.blocking import BlockingScheduler
from tools.strategy_exporter import export_strategy
import os
from dotenv import load_dotenv

load_dotenv()

def scheduled_export():
    print("Running scheduled export...")
    # This is a placeholder for getting the strategy file path
    strategy_file = "SampleStrategy.cs"
    export_strategy(strategy_file, "strategy_summary.md")

def main():
    if os.getenv("EXPORT_STRATEGY_SUMMARY", "false").lower() != "true":
        print("Scheduled export is disabled.")
        return

    scheduler = BlockingScheduler()

    if os.getenv("EXPORT_DAILY_ENABLED", "false").lower() == "true":
        daily_time = os.getenv("EXPORT_DAILY_TIME", "17:00").split(':')
        scheduler.add_job(scheduled_export, 'cron', hour=daily_time[0], minute=daily_time[1])
        print(f"Scheduled daily export at {daily_time[0]}:{daily_time[1]}")

    if os.getenv("EXPORT_WEEKLY_ENABLED", "false").lower() == "true":
        weekly_day = os.getenv("EXPORT_WEEKLY_DAY", "sat")
        weekly_time = os.getenv("EXPORT_WEEKLY_TIME", "12:00").split(':')
        scheduler.add_job(scheduled_export, 'cron', day_of_week=weekly_day, hour=weekly_time[0], minute=weekly_time[1])
        print(f"Scheduled weekly export on {weekly_day} at {weekly_time[0]}:{weekly_time[1]}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()
