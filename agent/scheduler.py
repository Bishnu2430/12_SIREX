import time
from datetime import datetime

class Scheduler:
    def __init__(self, controller, interval_sec=3600):
        """
        controller: AgentController instance
        interval_sec: how often to run
        """
        self.controller = controller
        self.interval_sec = interval_sec
        self.running = False

    def task(self):
        """
        Placeholder for periodic task.
        Later this can scan stored media folders or re-run analysis.
        """
        print(f"[{datetime.utcnow().isoformat()}] Running scheduled intelligence task...")
        # Future: fetch new media, re-run pipeline

    def start(self):
        self.running = True
        print("Scheduler started.")

        while self.running:
            self.task()
            time.sleep(self.interval_sec)

    def stop(self):
        self.running = False
        print("Scheduler stopped.")
