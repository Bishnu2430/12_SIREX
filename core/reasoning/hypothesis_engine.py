class HypothesisEngine:
    def generate(self, entities, relationships, exposures):
        hypotheses = []
        for rel in relationships:
            if rel["type"] == "AFFILIATED_WITH":
                hypotheses.append({
                    "hypothesis": "Person may be affiliated with organization",
                    "confidence": 0.7,
                    "entities": [rel["from"], rel["to"]]
                })
        loc_exposures = [e for e in exposures if "Location" in e["type"]]
        if len(loc_exposures) > 2:
            hypotheses.append({
                "hypothesis": "Person may have routine presence at a location",
                "confidence": 0.75,
                "entities": [loc_exposures[0]["entity"]]
            })
        return hypotheses