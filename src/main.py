"module"

import time
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler


def tick():
    "function"
    print(f"The time is: {datetime.now()}")


def main():
    "function"
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


if __name__ == "__main__":
    main()
