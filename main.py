from core.nodes import Node
from core.edges import Edge
from core.confidence import calculate_confidence
from core.graph_engine import KnowledgeGraph
from core.inference import InferenceRecord
from core.fingerprint.face_matcher import FaceMatcher
from core.pipelines.image_pipeline import process_image

kg = KnowledgeGraph()
face_matcher = FaceMatcher()

# CREATE DIVERSE NODES

image_node = Node(type="image", value="image_001.jpg", source="user_upload")
face_node = Node(type="face_embedding", value="face_vec_abc", source="model_output")
username_node = Node(type="username", value="shadow_recon", source="discovery_module")
ip_node = Node(type="ip", value="192.168.1.24", source="spiderfoot")
domain_node = Node(type="domain", value="example.com", source="spiderfoot")
audio_node = Node(type="audio_signature", value="audio_sig_xyz", source="model_output")
video_node = Node(type="video_frame_cluster", value="video_cluster_01", source="model_output")

img_id = kg.add_node(image_node)
face_id = kg.add_node(face_node)
user_id = kg.add_node(username_node)
ip_id = kg.add_node(ip_node)
domain_id = kg.add_node(domain_node)
audio_id = kg.add_node(audio_node)
video_id = kg.add_node(video_node)

# CREATE INTELLIGENCE EDGES

# Image -> Face
conf1 = calculate_confidence("model_output", "face_embedding", 0.92, 2)
edge1 = Edge(img_id, face_id, "derived_from", conf1,
             "Face embedding extracted from image", "face_embedding")

# Username -> Domain
conf2 = calculate_confidence("spiderfoot", "username_similarity", 0.7, 1)
edge2 = Edge(user_id, domain_id, "uses_infrastructure", conf2,
             "Username found associated with domain", "username_similarity")

# Domain -> IP
conf3 = calculate_confidence("spiderfoot", "perceptual_hash", 0.85, 2)
edge3 = Edge(domain_id, ip_id, "hosted_on", conf3,
             "DNS resolution", "dns_lookup")

# Video -> Audio correlation
conf4 = calculate_confidence("model_output", "time_correlation", 0.8, 1)
edge4 = Edge(video_id, audio_id, "co_occurs_with", conf4,
             "Audio track linked to video frames", "time_correlation")

kg.add_edge(edge1)
kg.add_edge(edge2)
kg.add_edge(edge3)
kg.add_edge(edge4)

# RECORD INFERENCE

inf = InferenceRecord(
    hypothesis="Image, username, and infrastructure may relate to same entity",
    nodes_involved=[img_id, face_id, user_id, domain_id, ip_id],
    edges_created=[edge1.id, edge2.id, edge3.id],
    agent_reasoning="Cross-domain artifact expansion",
    confidence=0.61,
    status="accepted"
)

kg.add_inference(inf)

# SHOW INTELLIGENCE VIEW

print("\n--- GRAPH RELATIONSHIPS ---")
for node_id, node in kg.nodes.items():
    relations = kg.find_related(node_id)
    if relations:
        print(f"\nNode ({node.type}) {node.value}")
        for rel in relations:
            print("  ->", rel)


from core.graph_engine import KnowledgeGraph
from core.fingerprint.face_matcher import FaceMatcher
from core.pipelines.image_pipeline import process_image

kg = KnowledgeGraph()
face_matcher = FaceMatcher()

# Run pipeline twice to simulate match
process_image("test1.jpg", kg, face_matcher)
process_image("test2.jpg", kg, face_matcher)

print("\n--- Graph Summary ---")
print("Nodes:", len(kg.nodes))
print("Edges:", len(kg.edges))
print("Inferences:", len(kg.inferences))


from core.graph_engine import KnowledgeGraph
from core.fingerprint.face_matcher import FaceMatcher
from core.pipelines.image_pipeline import process_image
from core.agent.agent_controller import OSINTAgent

kg = KnowledgeGraph()
face_matcher = FaceMatcher()
agent = OSINTAgent(kg)

# Initial input
process_image("test1.jpg", kg, face_matcher)

# Agent loop
for i in range(3):
    decision = agent.run_cycle()
    if not decision:
        break

    primitive, node = decision
    print(f"\n[Agent] Selected {node.type} ({node.value}) → {primitive}")


from core.graph_engine import KnowledgeGraph
from core.fingerprint.face_matcher import FaceMatcher
from core.agent.agent_controller import OSINTAgent
from core.agent.pipeline_runner import PipelineRunner
from core.pipelines.image_pipeline import process_image

kg = KnowledgeGraph()
face_matcher = FaceMatcher()
runner = PipelineRunner(kg, face_matcher)
agent = OSINTAgent(kg, runner)

# Initial seed
process_image("test1.jpg", kg, face_matcher)

# Recursive investigation
for i in range(5):
    result = agent.run_cycle()
    if not result:
        break

print("\n--- FINAL GRAPH STATS ---")
print("Nodes:", len(kg.nodes))
print("Edges:", len(kg.edges))
print("Inferences:", len(kg.inferences))

from core.analysis.graph_intelligence import (
    reinforce_confidence,
    detect_entity_merges,
    compute_risk_scores
)

# After recursive investigation finishes

reinforce_confidence(kg)
merges = detect_entity_merges(kg)
risk_scores = compute_risk_scores(kg)

print("\n--- ENTITY MERGE CANDIDATES ---")
print(merges)

print("\n--- RISK SCORES ---")
for node_id, score in risk_scores.items():
    print(kg.get_node(node_id).value, "→", round(score, 2))

from core.agent.memory import InvestigationMemory

memory = InvestigationMemory()
agent = OSINTAgent(kg, runner, memory)
