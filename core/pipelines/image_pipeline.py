from core.fingerprint.image_fingerprint import *
from core.nodes import Node
from core.edges import Edge
from core.confidence import calculate_confidence
from core.inference import InferenceRecord


def process_image(image_path, kg, face_matcher):

    # ---------- IMAGE NODE ----------
    image_node = Node(type="image", value=image_path, source="user_upload")
    img_id = kg.add_node(image_node)

    # ---------- PERCEPTUAL HASH ----------
    phash = get_perceptual_hash(image_path)
    hash_node = Node(type="image_hash", value=phash, source="model_output")
    hash_id = kg.add_node(hash_node)

    edge_conf = calculate_confidence("model_output", "perceptual_hash", 0.9, 1)
    kg.add_edge(Edge(img_id, hash_id, "derived_from", edge_conf,
                     "Perceptual hash generated", "perceptual_hash"))

    # ---------- FACE EMBEDDINGS ----------
    faces = extract_face_embeddings(image_path)
    created_edges = []

    for emb in faces:
        face_node = Node(type="face_embedding", value=str(emb[:5]), source="model_output")
        face_id = kg.add_node(face_node)

        conf = calculate_confidence("model_output", "face_embedding", 0.92, 1)
        edge = Edge(img_id, face_id, "derived_from", conf,
                    "Face embedding extracted", "face_embedding")
        edge_id = kg.add_edge(edge)
        created_edges.append(edge_id)

        # ---------- FACE MATCHING ----------
        match_id, score = face_matcher.find_match(emb)
        face_matcher.register_face(face_id, emb)

        if match_id and score > face_matcher.threshold:
            match_conf = calculate_confidence("model_output", "face_embedding", score, 2)
            kg.add_edge(Edge(face_id, match_id, "likely_same_as",
                             match_conf,
                             f"Face similarity match {score:.2f}",
                             "face_embedding"))

    # ---------- INFERENCE RECORD ----------
    inf = InferenceRecord(
        hypothesis="Image expanded into visual artifacts",
        nodes_involved=[img_id, hash_id],
        edges_created=created_edges,
        agent_reasoning="Initial visual OSINT expansion",
        confidence=0.7,
        status="accepted"
    )
    kg.add_inference(inf)

    return img_id
