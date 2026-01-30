import uuid

class ExposureMapper:
    def __init__(self):
        pass

    def biometric_exposure(self, persons):
        exposures = []
        for person in persons:
            exposures.append({
                "exposure_id": f"EXP_{uuid.uuid4().hex[:8]}",
                "type": "Biometric Identity Exposure",
                "entity": person["entity_id"],
                "confidence": person.get("face_confidence", 0),
                "signals": ["face_detection"]
            })
        return exposures

    def location_exposure(self, locations):
        exposures = []
        for loc in locations:
            if loc.get("gps"):
                exposures.append({
                    "exposure_id": f"EXP_{uuid.uuid4().hex[:8]}",
                    "type": "Precise Geolocation Exposure",
                    "entity": loc["entity_id"],
                    "confidence": 1.0,
                    "signals": ["metadata_gps"]
                })
            elif loc.get("landmark"):
                exposures.append({
                    "exposure_id": f"EXP_{uuid.uuid4().hex[:8]}",
                    "type": "Inferred Location Exposure",
                    "entity": loc["entity_id"],
                    "confidence": loc.get("confidence", 0),
                    "signals": ["landmark_similarity"]
                })
        return exposures

    def organizational_exposure(self, orgs):
        exposures = []
        for org in orgs:
            exposures.append({
                "exposure_id": f"EXP_{uuid.uuid4().hex[:8]}",
                "type": "Organizational Affiliation Exposure",
                "entity": org["entity_id"],
                "confidence": org.get("confidence", 0),
                "signals": ["ocr_text"]
            })
        return exposures

    def behavioral_exposure(self, events):
        exposures = []
        for event in events:
            exposures.append({
                "exposure_id": f"EXP_{uuid.uuid4().hex[:8]}",
                "type": "Behavioral Activity Exposure",
                "entity": event["entity_id"],
                "confidence": 0.7,
                "signals": ["scene", "objects"]
            })
        return exposures

    def build_all(self, entities):
        exposures = []
        exposures += self.biometric_exposure(entities.get("persons", []))
        exposures += self.location_exposure(entities.get("locations", []))
        exposures += self.organizational_exposure(entities.get("organizations", []))
        exposures += self.behavioral_exposure(entities.get("events", []))
        return exposures
