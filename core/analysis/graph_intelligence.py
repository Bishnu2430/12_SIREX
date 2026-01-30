def reinforce_confidence(kg):

    relation_map = {}

    for edge in kg.edges.values():
        key = (edge.from_node, edge.to_node, edge.relation)
        relation_map.setdefault(key, []).append(edge)

    for key, edges in relation_map.items():
        if len(edges) > 1:
            boost = min(0.2, 0.05 * len(edges))
            for e in edges:
                e.confidence = min(1.0, e.confidence + boost)

def detect_entity_merges(kg):

    merges = []

    for e in kg.edges.values():
        if e.relation == "likely_same_as" and e.confidence > 0.7:
            merges.append((e.from_node, e.to_node))

    return merges

def compute_centrality(kg):

    centrality = {}

    for node_id in kg.nodes:
        centrality[node_id] = sum(
            1 for e in kg.edges.values()
            if e.from_node == node_id or e.to_node == node_id
        )

    return centrality

def compute_risk_scores(kg):

    centrality = compute_centrality(kg)
    risk_scores = {}

    for node_id, node in kg.nodes.items():
        base = node.confidence
        influence = centrality.get(node_id, 1) * 0.1

        if node.type in ["ip", "domain"]:
            risk = base + influence + 0.2
        elif node.type in ["username", "face_embedding"]:
            risk = base + influence + 0.3
        else:
            risk = base + influence

        risk_scores[node_id] = min(1.0, risk)

    return risk_scores
