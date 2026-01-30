class RelationshipMapper:
    def __init__(self):
        pass

    def map_person_location(self, persons, locations):
        relationships = []

        for person in persons:
            for loc in locations:
                relationships.append({
                    "from": person["entity_id"],
                    "to": loc["entity_id"],
                    "type": "AT_LOCATION"
                })

        return relationships

    def map_person_org(self, persons, orgs, ocr_text):
        relationships = []

        for person in persons:
            for org in orgs:
                relationships.append({
                    "from": person["entity_id"],
                    "to": org["entity_id"],
                    "type": "AFFILIATED_WITH"
                })

        return relationships

    def map_person_event(self, persons, events):
        relationships = []

        for person in persons:
            for event in events:
                relationships.append({
                    "from": person["entity_id"],
                    "to": event["entity_id"],
                    "type": "PART_OF_EVENT"
                })

        return relationships

    def map_event_location(self, events, locations):
        relationships = []

        for event in events:
            for loc in locations:
                relationships.append({
                    "from": event["entity_id"],
                    "to": loc["entity_id"],
                    "type": "EVENT_AT_LOCATION"
                })

        return relationships

    def build_all(self, entities, signals=None):
        persons = entities.get("persons", [])
        locations = entities.get("locations", [])
        orgs = entities.get("organizations", [])
        events = entities.get("events", [])

        relationships = []
        relationships += self.map_person_location(persons, locations)
        relationships += self.map_person_org(persons, orgs, signals.get("ocr_text", []) if signals else [])
        relationships += self.map_person_event(persons, events)
        relationships += self.map_event_location(events, locations)

        return relationships
