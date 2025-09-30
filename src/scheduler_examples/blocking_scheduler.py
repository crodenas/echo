"""
A proof-of-concept for showing how APScheduler works.
"""

from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler


def tick():
    """
    A simple function that prints the current time.
    """
    print(f"The time is: {datetime.now()}")


if __name__ == "__main__":
    # Create a new scheduler
    scheduler = BlockingScheduler()

    # Add a job to the scheduler that will run the `tick` function every 3 seconds
    scheduler.add_job(tick, "interval", seconds=3)

    print("Scheduler started. Press Ctrl+C to exit.")

    try:
        # Start the scheduler
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        # Shut down the scheduler gracefully on exit
        print("Shutting down scheduler...")
        scheduler.shutdown()
        print("Scheduler shut down.")
