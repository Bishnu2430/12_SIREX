import json, os, logging
from datetime import datetime
logger = logging.getLogger(__name__)

class Observability:
    def __init__(self, log_dir="storage/logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def log_event(self, session_id, stage, data):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": stage,
            "data": data
        }
        log_file = os.path.join(self.log_dir, f"{session_id}.log")
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry, default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    def log_pipeline(self, session_id, signals, entities, exposures, risk_results):
        self.log_event(session_id, "signals_detected", signals)
        self.log_event(session_id, "entities_built", entities)
        self.log_event(session_id, "exposures_mapped", exposures)
        self.log_event(session_id, "risk_assessment", risk_results)

    def log_learning(self, session_id, entity_id, action):
        self.log_event(session_id, "learning_update", {
            "entity_id": entity_id,
            "action": action
        })
    
    def get_logs(self, session_id):
        """Retrieve logs for a session"""
        log_file = os.path.join(self.log_dir, f"{session_id}.log")
        if not os.path.exists(log_file):
            return []
        logs = []
        try:
            with open(log_file, "r") as f:
                for line in f:
                    logs.append(json.loads(line.strip()))
        except:
            pass
        return logs