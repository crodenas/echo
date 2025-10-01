"module"

import time
from datetime import datetime

from scheduler import BackgroundSchedulerFactory


def tick():
    "function"
    print(f"The time is: {datetime.now()}")


# Need to understnad how it loads when it is re started
# Need to understand what the skip misfires does to the emails
# Can a notification receive the next run time to include in the email?


def main():
    "function"

    scheduler = BackgroundSchedulerFactory.create_scheduler(name="main")

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
