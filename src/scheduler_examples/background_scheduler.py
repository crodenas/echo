"""
A proof-of-concept for showing how BackgroundScheduler works.
"""

import time
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler


def tick():
    """
    A simple function that prints the current time.
    """
    print(f"The time is: {datetime.now()}")


if __name__ == "__main__":
    # Create a new scheduler that runs in the background
    scheduler = BackgroundScheduler()

    # Add a job to the scheduler that will run the `tick` function every 3 seconds
    scheduler.add_job(tick, "interval", seconds=3)

    # Start the scheduler
    scheduler.start()

    print("Scheduler started. Press Ctrl+C to exit.")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        # Shut down the scheduler gracefully on exit
        print("Shutting down scheduler...")
        scheduler.shutdown()
        print("Scheduler shut down.")
