class MisuseSimulator:
    def __init__(self):
        pass

    def simulate_biometric_misuse(self, exposure):
        return {
            "entity": exposure["entity"],
            "misuse": "Identity impersonation using synthetic media",
            "impact": "Fraud, social engineering, unauthorized access attempts",
            "likelihood": "High"
        }

    def simulate_location_misuse(self, exposure):
        if "Precise" in exposure["type"]:
            likelihood = "High"
            impact = "Physical targeting, stalking, burglary timing"
        else:
            likelihood = "Medium"
            impact = "Routine tracking and profiling"

        return {
            "entity": exposure["entity"],
            "misuse": "Location-based targeting and movement profiling",
            "impact": impact,
            "likelihood": likelihood
        }

    def simulate_org_misuse(self, exposure):
        return {
            "entity": exposure["entity"],
            "misuse": "Spear-phishing and impersonation of organizational role",
            "impact": "Credential theft, internal system compromise",
            "likelihood": "High"
        }

    def simulate_behavioral_misuse(self, exposure):
        return {
            "entity": exposure["entity"],
            "misuse": "Behavioral profiling and reputation manipulation",
            "impact": "Blackmail, targeted social engineering",
            "likelihood": "Medium"
        }

    def run(self, exposures):
        misuse_cases = []

        for exp in exposures:
            if "Biometric" in exp["type"]:
                misuse_cases.append(self.simulate_biometric_misuse(exp))

            elif "Geolocation" in exp["type"] or "Location" in exp["type"]:
                misuse_cases.append(self.simulate_location_misuse(exp))

            elif "Organizational" in exp["type"]:
                misuse_cases.append(self.simulate_org_misuse(exp))

            elif "Behavioral" in exp["type"]:
                misuse_cases.append(self.simulate_behavioral_misuse(exp))

        return misuse_cases
