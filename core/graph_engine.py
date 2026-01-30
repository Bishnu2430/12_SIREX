from typing import Dict
from .nodes import Node
from .edges import Edge
from .inference import InferenceRecord


class KnowledgeGraph:

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.inferences: Dict[str, InferenceRecord] = {}

    # ---------- NODE OPERATIONS ----------
    def add_node(self, node: Node):
        self.nodes[node.id] = node
        return node.id

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    # ---------- EDGE OPERATIONS ----------
    def add_edge(self, edge: Edge):
        self.edges[edge.id] = edge
        return edge.id

    def get_edges_from(self, node_id):
        return [e for e in self.edges.values() if e.from_node == node_id]

    # ---------- INFERENCE TRACKING ----------
    def add_inference(self, record: InferenceRecord):
        self.inferences[record.id] = record
        return record.id

    # ---------- GRAPH INTELLIGENCE ----------
    def find_related(self, node_id):
        return [
            (e.relation, self.nodes[e.to_node].value, e.confidence)
            for e in self.get_edges_from(node_id)
        ]
