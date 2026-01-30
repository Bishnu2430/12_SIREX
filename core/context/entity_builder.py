import uuid

class EntityBuilder:
    def __init__(self):
        pass

    def build_person_entities(self, faces, embeddings):
        persons = []

        for i, face in enumerate(faces):
            person_id = f"Person_{uuid.uuid4().hex[:8]}"

            persons.append({
                "entity_id": person_id,
                "type": "Person",
                "face_bbox": face["bbox"],
                "face_confidence": face["confidence"],
                "embedding": embeddings[i].tolist() if i < len(embeddings) else None
            })

        return persons

    def build_location_entities(self, scene_info, landmark_info, metadata):
        locations = []

        if metadata.get("gps_latitude") and metadata.get("gps_longitude"):
            locations.append({
                "entity_id": f"Location_{uuid.uuid4().hex[:8]}",
                "type": "Location",
                "source": "metadata",
                "gps": {
                    "lat": metadata["gps_latitude"],
                    "lon": metadata["gps_longitude"]
                }
            })

        for scene in scene_info:
            locations.append({
                "entity_id": f"Location_{uuid.uuid4().hex[:8]}",
                "type": "Location",
                "source": "scene",
                "scene_label": scene["scene"],
                "confidence": scene["confidence"]
            })

        for lm in landmark_info:
            locations.append({
                "entity_id": f"Location_{uuid.uuid4().hex[:8]}",
                "type": "Location",
                "source": "landmark_similarity",
                "landmark": lm["landmark"],
                "confidence": lm["similarity"]
            })

        return locations

    def build_organization_entities(self, ocr_text):
        orgs = []

        keywords = ["corp", "ltd", "inc", "university", "bank", "company"]

        for item in ocr_text:
            text_lower = item["text"].lower()
            if any(k in text_lower for k in keywords):
                orgs.append({
                    "entity_id": f"Org_{uuid.uuid4().hex[:8]}",
                    "type": "Organization",
                    "name": item["text"],
                    "confidence": item["confidence"]
                })

        return orgs

    def build_event_entities(self, scene_info, objects):
        events = []

        crowded = any(obj["label"] == "person" for obj in objects)
        outdoor = any("outdoor" in s["scene"].lower() for s in scene_info)

        if crowded and outdoor:
            events.append({
                "entity_id": f"Event_{uuid.uuid4().hex[:8]}",
                "type": "Event",
                "description": "Possible public gathering"
            })

        return events

    def build_all(self, signals):
        return {
            "persons": self.build_person_entities(signals["faces"], signals["embeddings"]),
            "locations": self.build_location_entities(
                signals["scene"], signals["landmarks"], signals["metadata"]
            ),
            "organizations": self.build_organization_entities(signals["ocr_text"]),
            "events": self.build_event_entities(signals["scene"], signals["objects"])
        }
