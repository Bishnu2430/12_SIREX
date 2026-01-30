class RiskEngine:
    def __init__(self):
        self.weights = {
            "sensitivity": 0.3,
            "exploitability": 0.25,
            "visibility": 0.15,
            "correlation": 0.15,
            "ai_amplification": 0.15
        }

    def score_exposure(self, exposure_type):
        if "Biometric" in exposure_type:
            return {"sensitivity": 1.0, "exploitability": 0.9, "ai_amplification": 1.0}
        if "Precise Geolocation" in exposure_type:
            return {"sensitivity": 0.9, "exploitability": 0.8, "ai_amplification": 0.6}
        if "Inferred Location" in exposure_type:
            return {"sensitivity": 0.7, "exploitability": 0.6, "ai_amplification": 0.5}
        if "Organizational" in exposure_type:
            return {"sensitivity": 0.8, "exploitability": 0.8, "ai_amplification": 0.7}
        if "Behavioral" in exposure_type:
            return {"sensitivity": 0.6, "exploitability": 0.5, "ai_amplification": 0.5}
        return {"sensitivity": 0.5, "exploitability": 0.5, "ai_amplification": 0.5}

    def compute_risk(self, exposure, misuse):
        base_scores = self.score_exposure(exposure["type"])
        visibility = 0.8
        correlation = 0.7
        risk_score = (
            base_scores["sensitivity"] * self.weights["sensitivity"] +
            base_scores["exploitability"] * self.weights["exploitability"] +
            visibility * self.weights["visibility"] +
            correlation * self.weights["correlation"] +
            base_scores["ai_amplification"] * self.weights["ai_amplification"]
        )
        return round(risk_score, 2)

    def classify_severity(self, score):
        if score >= 0.75:
            return "CRITICAL"
        elif score >= 0.6:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

    def evaluate(self, exposures, misuse_cases):
        results = []
        for exp in exposures:
            misuse = next((m for m in misuse_cases if m["entity"] == exp["entity"]), None)
            score = self.compute_risk(exp, misuse)
            severity = self.classify_severity(score)
            results.append({
                "entity": exp["entity"],
                "exposure_type": exp["type"],
                "risk_score": score,
                "severity": severity
            })
        return results