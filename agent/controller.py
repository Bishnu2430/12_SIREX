from core.context.entity_builder import EntityBuilder
from core.context.relationship_mapper import RelationshipMapper
from core.exposure.exposure_mapper import ExposureMapper
from core.exposure.misuse_simulator import MisuseSimulator
from core.exposure.risk_engine import RiskEngine
from core.reporting.report_generator import ReportGenerator
from agent.memory import AgentMemory
from agent.observability import Observability
from graph.neo4j_client import Neo4jClient
from storage.postgres import PostgresStorage
from core.reasoning.hypothesis_engine import HypothesisEngine
from core.reasoning.behavior_analysis import BehaviorAnalyzer
from core.reasoning.spatial_temporal import SpatialTemporalReasoner


class AgentController:
    def __init__(self):
        self.entity_builder = EntityBuilder()
        self.relationship_mapper = RelationshipMapper()
        self.exposure_mapper = ExposureMapper()
        self.misuse_simulator = MisuseSimulator()
        self.risk_engine = RiskEngine()
        self.report_generator = ReportGenerator()
        self.memory = AgentMemory()
        self.hypothesis_engine = HypothesisEngine()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.spatial_reasoner = SpatialTemporalReasoner()
        self.observer = Observability()
        self.graph = Neo4jClient()
        self.storage = PostgresStorage()



    def run_pipeline(self, signals, session_id):
        self.observer.log_event(session_id, "pipeline_start", {"session_id": session_id})

        entities = self.entity_builder.build_all(signals)
        self.observer.log_event(session_id, "entities_built", entities)

        relationships = self.relationship_mapper.build_all(entities, signals)
        self.observer.log_event(session_id, "relationships_built", relationships)

        exposures = self.exposure_mapper.build_all(entities)
        self.observer.log_event(session_id, "exposures_mapped", exposures)

        misuse_cases = self.misuse_simulator.run(exposures)
        self.observer.log_event(session_id, "misuse_simulated", misuse_cases)

        risk_results = self.risk_engine.evaluate(exposures, misuse_cases)
        self.observer.log_event(session_id, "risk_assessed", risk_results)

        report = self.report_generator.generate(
            entities, exposures, misuse_cases, risk_results
        )

        # Store in graph
        self.graph.store_entities(entities)
        self.graph.store_relationships(relationships)
        self.graph.store_exposures(exposures)

        # Store report in database
        self.storage.save_report(session_id, report)

        # Memory learning
        for person in entities.get("persons", []):
            if person.get("embedding"):
                match = self.memory.find_match(person["embedding"])
                if not match:
                    self.memory.store_person(person["entity_id"], person["embedding"], session_id)
                    self.observer.log_learning(session_id, person["entity_id"], "new_entity_stored")

        self.observer.log_event(session_id, "pipeline_complete", {"status": "success"})
        
        # --- REASONING LAYER ---
        hypotheses = self.hypothesis_engine.generate(entities, relationships, exposures)
        behavior_patterns = self.behavior_analyzer.analyze(exposures)
        spatial_temporal_insights = self.spatial_reasoner.analyze(
            signals.get("metadata", {}), entities.get("locations", [])
        )

        self.observer.log_event(session_id, "hypotheses_generated", hypotheses)
        self.observer.log_event(session_id, "behavior_patterns_detected", behavior_patterns)
        self.observer.log_event(session_id, "spatial_temporal_insights", spatial_temporal_insights)
        
        report = self.report_generator.generate(
            entities, exposures, misuse_cases, risk_results,
            hypotheses=hypotheses,
            behavior_patterns=behavior_patterns,
            spatial_temporal_insights=spatial_temporal_insights
        )

        return {
            "entities": entities,
            "relationships": relationships,
            "report": report
        }
        
        

