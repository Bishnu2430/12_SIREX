import time, logging
from datetime import datetime
logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, controller, interval_sec=3600):
        self.controller = controller
        self.interval_sec = interval_sec
        self.running = False

    def task(self):
        logger.info(f"[{datetime.utcnow().isoformat()}] Running scheduled intelligence task...")

    def start(self):
        self.running = True
        logger.info("Scheduler started.")
        while self.running:
            self.task()
            time.sleep(self.interval_sec)

    def stop(self):
        self.running = False
        logger.info("Scheduler stopped.")