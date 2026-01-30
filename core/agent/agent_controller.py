from core.inference import InferenceRecord
from core.agent.heuristics import score_node_for_expansion


class OSINTAgent:

    def __init__(self, kg, runner, memory):
        self.kg = kg
        self.runner = runner
        self.memory = memory
        self.visited = set()

    def choose_next_target(self):
        scored = []

        for node in self.kg.nodes.values():
            score = score_node_for_expansion(node)
            scored.append((node.id, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None

    def decide_primitive(self, node):
        if node.type == "image":
            return "image_fingerprint"
        if node.type == "face_embedding":
            return "face_analysis"
        if node.type == "username":
            return "identity_osint"
        if node.type in ["domain", "ip"]:
            return "infrastructure_osint"
        return None

    def run_cycle(self):
        target_id = self.choose_next_target()
        if not target_id:
            return None

        node = self.kg.get_node(target_id)
        primitive = self.decide_primitive(node)

        # Record reasoning
        inf = InferenceRecord(
            hypothesis=f"Agent selected node {node.value} for expansion",
            nodes_involved=[target_id],
            edges_created=[],
            agent_reasoning=f"High heuristic expansion score; chose primitive {primitive}",
            confidence=0.6,
            status="accepted"
        )

        self.kg.add_inference(inf)
        
        self.runner.execute(primitive, node)

        return primitive, node

class OSINTAgent:

    def __init__(self, kg, runner, memory):
        self.kg = kg
        self.runner = runner
        self.memory = memory
        self.visited = set()

    def choose_next_target(self):
        scored = []

        for node in self.kg.nodes.values():
            base_score = score_node_for_expansion(node)
            learning_boost = self.memory.node_type_score(node.type)
            scored.append((node.id, base_score * learning_boost))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None

    def run_cycle(self):
        target_id = self.choose_next_target()
        if not target_id or target_id in self.visited:
            return None

        node = self.kg.get_node(target_id)
        primitive = self.decide_primitive(node)

        self.visited.add(target_id)

        # Execute
        before_nodes = len(self.kg.nodes)
        self.runner.execute(primitive, node)
        after_nodes = len(self.kg.nodes)

        success = after_nodes > before_nodes
        self.memory.record_result(node.type, primitive, success)

        return primitive, node
