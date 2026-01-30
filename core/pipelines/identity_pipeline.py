from core.nodes import Node
from core.edges import Edge
from core.confidence import calculate_confidence
from core.inference import InferenceRecord
from .identity_utils import generate_variants, probe_platforms


def process_username(username_node, kg):

    username = username_node.value
    variants = generate_variants(username)

    created_nodes = []
    created_edges = []

    for var in variants:
        results = probe_platforms(var)

        for res in results:
            platform_node = Node(type="platform", value=res["platform"], source="identity_osint")
            profile_node = Node(type="profile_url", value=res["profile_url"], source="identity_osint")

            pid = kg.add_node(platform_node)
            uid = kg.add_node(profile_node)

            conf = calculate_confidence("heuristic", "username_similarity", 0.75, 1)

            e1 = Edge(username_node.id, uid, "co_occurs_with", conf,
                      "Username linked to profile", "username_probe")
            e2 = Edge(uid, pid, "indexed_by", conf,
                      "Profile hosted on platform", "platform_link")

            kg.add_edge(e1)
            kg.add_edge(e2)

            created_nodes.extend([pid, uid])
            created_edges.extend([e1.id, e2.id])

    inf = InferenceRecord(
        hypothesis=f"Username {username} expanded into platform identities",
        nodes_involved=[username_node.id] + created_nodes,
        edges_created=created_edges,
        agent_reasoning="Agent executed identity OSINT primitive",
        confidence=0.65,
        status="accepted"
    )

    kg.add_inference(inf)
