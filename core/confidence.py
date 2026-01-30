SOURCE_RELIABILITY = {
    "model_output": 0.8,
    "spiderfoot": 0.6,
    "external_api": 0.7,
    "heuristic": 0.5
}

METHOD_RELIABILITY = {
    "face_embedding": 0.85,
    "perceptual_hash": 0.75,
    "username_similarity": 0.6,
    "time_correlation": 0.55
}


def calculate_confidence(source, method, signal_strength, supporting_edges=1):
    sr = SOURCE_RELIABILITY.get(source, 0.5)
    mr = METHOD_RELIABILITY.get(method, 0.5)
    correlation_support = min(1.0, supporting_edges * 0.15)

    return round(sr * mr * signal_strength * correlation_support, 3)
