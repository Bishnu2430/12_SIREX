class BehaviorAnalyzer:
    def analyze(self, exposures):
        behavior_patterns = []
        location_exposures = [e for e in exposures if "Location" in e["type"]]
        if len(location_exposures) > 3:
            behavior_patterns.append({
                "pattern": "Frequent location exposure",
                "risk_implication": "Routine predictability",
                "severity": "HIGH"
            })
        event_exposures = [e for e in exposures if "Behavioral" in e["type"]]
        if event_exposures:
            behavior_patterns.append({
                "pattern": "Participation in public events",
                "risk_implication": "Social profiling risk",
                "severity": "MEDIUM"
            })
        return behavior_patterns