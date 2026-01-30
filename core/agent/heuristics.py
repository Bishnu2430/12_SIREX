def score_node_for_expansion(node):
    """
    Determines how valuable a node is for further OSINT expansion
    """

    type_priority = {
        "image": 0.9,
        "face_embedding": 0.95,
        "username": 0.85,
        "domain": 0.8,
        "ip": 0.75,
        "audio_signature": 0.7,
        "video_frame_cluster": 0.7,
    }

    base = type_priority.get(node.type, 0.5)

    # Higher confidence = more promising
    return base * node.confidence
