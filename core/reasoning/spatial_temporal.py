class SpatialTemporalReasoner:
    def analyze(self, metadata, locations):
        insights = []

        timestamp = metadata.get("timestamp")

        if timestamp:
            insights.append({
                "insight": "Media timestamp available",
                "risk": "Time-based tracking possible"
            })

        for loc in locations:
            if loc.get("gps"):
                insights.append({
                    "insight": "Precise geolocation + timestamp",
                    "risk": "Movement pattern inference"
                })

        return insights
