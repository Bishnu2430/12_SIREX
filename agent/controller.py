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
from core.vision.object_detection import ObjectDetector
from core.vision.face_detection import FaceDetector
from core.vision.ocr_reader import OCRReader
from core.reasoning.spatial_temporal import SpatialTemporalReasoner
from core.exposures import ExposureAnalyzer
import logging

logger = logging.getLogger(__name__)

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
        from core.reasoning.llm_client import LLMClient
        self.llm_client = LLMClient()
        
        # NEW: Exposure-Centric Analysis (Primary)
        self.exposure_analyzer = ExposureAnalyzer()
        
        # Tools
        self.object_detector = ObjectDetector()
        self.face_detector = FaceDetector()
        self.ocr_reader = OCRReader()
        self.graph = Neo4jClient()
        self.storage = PostgresStorage()
        self.latest_graph_data = {"nodes": [], "links": []}

    def _build_memory_graph(self, entities, relationships):
        nodes = []
        links = []
        node_ids = set()

        for category, items in entities.items():
            for item in items:
                if item["entity_id"] not in node_ids:
                    nodes.append({"id": item["entity_id"], "type": item["type"]})
                    node_ids.add(item["entity_id"])
        
        for rel in relationships:
            # Ensure source/target exist in nodes (they should)
            links.append({
                "source": rel["from"],
                "target": rel["to"],
                "type": rel["type"]
            })
            
        return {"nodes": nodes, "links": links}

    def run_pipeline(self, signals, session_id, image_path=None): # Added image_path
        logger.info(f"Starting pipeline for session: {session_id}")
        self.observer.log_event(session_id, "pipeline_start", {"session_id": session_id})

        # Run Local Vision Models (Parallel-ish execution logic here or sequential for simplicity)
        vision_results = {}
        if image_path:
            # YOLO
            vision_results["objects"] = self.object_detector.detect(image_path)
            
            # Face
            vision_results["faces"] = self.face_detector.detect(image_path)
            
            # OCR
            vision_results["ocr"] = self.ocr_reader.read_text(image_path)

        signals.update(vision_results)
        self.observer.log_event(session_id, "vision_analysis_complete", {k: len(v) if isinstance(v, list) else "Data" for k, v in vision_results.items()})

        # PRIMARY: Exposure-Centric Analysis (Rule-Based, Reliable)
        exposure_report = self.exposure_analyzer.analyze(signals)
        self.observer.log_event(session_id, "exposure_analysis_complete", {
            "total_exposures": exposure_report.total_count,
            "by_severity": exposure_report.by_severity
        })
        
        # OPTIONAL: LLM Analysis (if API is available)
        llm_result = None
        narrative_report = ""
        llm_exposures = []
        reasoning_trace = ""
        
        try:
            llm_result = self.llm_client.analyze_signals(signals, image_path=image_path)
            narrative_report = llm_result.get("narrative_report", "")
            llm_exposures = llm_result.get("exposures", [])
            reasoning_trace = llm_result.get("reasoning_trace", "")
            self.observer.log_event(session_id, "llm_analysis_complete", {"status": "success"})
            if reasoning_trace:
                self.observer.log_event(session_id, "agent_reasoning_trace", {"trace": reasoning_trace})
        except Exception as llm_error:
            logger.warning(f"LLM analysis unavailable: {llm_error}")
            self.observer.log_event(session_id, "llm_analysis_skipped", {"reason": str(llm_error)})

        # Entity Building (Graph)
        entities = self.entity_builder.build_all(signals)
        
        # ----------------------------------------------------
        # ENTITY RE-IDENTIFICATION & PERSISTENCE (MEMORY)
        # ----------------------------------------------------
        # 1. Persons (Biometric Re-ID)
        for person in entities.get("persons", []):
            if person.get("embedding"):
                match_id = self.memory.find_match(person["embedding"])
                if match_id:
                    logger.info(f"Re-identified Person: {match_id}")
                    person["entity_id"] = match_id
                    person["reidentified"] = True
                else:
                    self.memory.store_person(person["entity_id"], person["embedding"], session_id)

        # 2. Locations (Name/GPS Match) - Simple string match for now, could use vector search too
        # For now, we assume graph.neo4j handles MERGE by name, but we want to know if it's "known"
        # Since we don't have embeddings for locations implemented yet, we rely on Graph MERGE.
        # But we can tag them for the report.
        
        # 3. Events - Same as locations.
        
        self.observer.log_event(session_id, "entities_built", entities)

        relationships = self.relationship_mapper.build_all(entities, signals)
        self.observer.log_event(session_id, "relationships_built", relationships)

        # Map Exposures: Prefer LLM exposures, fallback to hardcoded
        if llm_exposures:
            exposures = []
            for exp in llm_exposures:
                # Normalize keys for report generator
                exposures.append({
                    "exposure_id": f"EXP_{uuid.uuid4().hex[:8]}",
                    "type": exp.get("type"),
                    "entity": "Analyzed Subject", # LLM usually analyzes the main subject
                    "risk_score": 0.9 if exp.get("risk_level") == "CRITICAL" else 0.7, # Simplified mapping
                    "severity": exp.get("risk_level", "MEDIUM"),
                    "simulated_misuse": {
                        "misuse": exp.get("misuse_scenario", "N/A"),
                        "impact": "See report details"
                    },
                    "recommendations": [exp.get("recommendation")]
                })
        else:
            exposures = self.exposure_mapper.build_all(entities)
        
        self.observer.log_event(session_id, "exposures_mapped", exposures)

        misuse_cases = self.misuse_simulator.run(exposures) if not llm_exposures else [] # LLM handled misuse
        risk_results = [] # LLM handled risk
        
        # Prepare Risk Results format for Report Generator
        if llm_exposures:
             for exp in exposures:
                 risk_results.append({
                     "entity": exp["entity"],
                     "exposure_type": exp["type"],
                     "risk_score": exp["risk_score"],
                     "severity": exp["severity"]
                 })
        else:
            risk_results = self.risk_engine.evaluate(exposures, misuse_cases)

        # Generate Reasoning Artifacts
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
            spatial_temporal_insights=spatial_temporal_insights,
            llm_analysis=narrative_report,
            raw_signals=signals
        )

        self.graph.store_entities(entities)
        self.graph.store_relationships(relationships)
        self.graph.store_exposures(exposures)
        
        # Update in-memory graph cache
        self.latest_graph_data = self._build_memory_graph(entities, relationships)

        self.storage.save_report(session_id, report)

        for person in entities.get("persons", []):
            if person.get("embedding"):
                match = self.memory.find_match(person["embedding"])
                if not match:
                    self.memory.store_person(person["entity_id"], person["embedding"], session_id)
                    self.observer.log_learning(session_id, person["entity_id"], "new_entity_stored")

        self.observer.log_event(session_id, "pipeline_complete", {"status": "success"})

        return {
            "entities": entities,
            "relationships": relationships,
            "exposures": exposures,
            "exposure_report": exposure_report.to_dict(),  # NEW: Rule-based exposure detection
            "risk_results": risk_results,
            "report": report
        }
