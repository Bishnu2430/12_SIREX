from datetime import datetime

class ReportGenerator:
    def __init__(self):
        pass

    def generate_recommendations(self, exposure_type, severity):
        if "Biometric" in exposure_type:
            return [
                "Limit public sharing of clear facial imagery",
                "Enable multi-factor authentication",
                "Monitor for impersonation attempts"
            ]

        if "Geolocation" in exposure_type or "Location" in exposure_type:
            return [
                "Strip metadata before posting media",
                "Avoid sharing real-time location updates",
                "Review privacy settings on social platforms"
            ]

        if "Organizational" in exposure_type:
            return [
                "Avoid displaying badges or internal documents publicly",
                "Educate staff on social engineering risks",
                "Verify identity before responding to credential requests"
            ]

        if "Behavioral" in exposure_type:
            return [
                "Reduce predictable posting patterns",
                "Avoid revealing routines publicly"
            ]

        return ["Review digital privacy practices"]

    def build_entity_summary(self, entities):
        return {
            "persons_detected": len(entities.get("persons", [])),
            "locations_detected": len(entities.get("locations", [])),
            "organizations_detected": len(entities.get("organizations", [])),
            "events_detected": len(entities.get("events", []))
        }

    def generate(self, entities, exposures, misuse_cases, risk_results,
             hypotheses=None, behavior_patterns=None, spatial_temporal_insights=None):

        report = {
            "report_generated_at": datetime.utcnow().isoformat(),
            "summary": self.build_entity_summary(entities),
            "exposure_analysis": [],
            "reasoning": {
                "hypotheses": hypotheses or [],
                "behavior_patterns": behavior_patterns or [],
                "spatial_temporal_insights": spatial_temporal_insights or []
            }
        }


        for risk in risk_results:
            exposure_type = risk["exposure_type"]
            entity = risk["entity"]

            misuse = next((m for m in misuse_cases if m["entity"] == entity), None)

            report["exposure_analysis"].append({
                "entity": entity,
                "exposure_type": exposure_type,
                "risk_score": risk["risk_score"],
                "severity": risk["severity"],
                "simulated_misuse": misuse,
                "recommendations": self.generate_recommendations(exposure_type, risk["severity"])
            })

        return report
