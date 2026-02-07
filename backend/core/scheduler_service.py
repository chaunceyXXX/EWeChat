import schedule
import time
import threading
from typing import Callable
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SchedulerService:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._job = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logging.info("Scheduler started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        logging.info("Scheduler stopped")

    def _run_loop(self):
        while not self._stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)

    def update_job(self, time_str: str, frequency: str, task_func: Callable):
        schedule.clear()
        self._job = None
        
        if frequency == 'daily':
            # time_str should be HH:MM
            self._job = schedule.every().day.at(time_str).do(task_func)
            logging.info(f"Scheduled daily job at {time_str}")
        elif frequency == 'hourly':
             # For demo/testing, interprets time_str as minutes past the hour if needed, 
             # but here we simplify to just "every hour" or custom interval if complex.
             # For MVP, let's assume 'hourly' means every hour.
             self._job = schedule.every().hour.do(task_func)
             logging.info("Scheduled hourly job")
        
        # Add more logic as needed for other frequencies

    def get_next_run(self):
        if self._job:
            return self._job.next_run
        return None

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()
