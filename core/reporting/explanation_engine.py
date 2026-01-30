class ExplanationEngine:
    def explain_risk(self, exposure_type, severity, misuse):
        explanation = f"This entity is exposed through {exposure_type}. "
        if misuse:
            explanation += f"A potential misuse includes: {misuse['misuse']}. "
        if severity in ["HIGH", "CRITICAL"]:
            explanation += "This presents a serious security and privacy concern."
        else:
            explanation += "This presents moderate exposure risk."
        return explanation