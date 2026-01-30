from collections import defaultdict


class InvestigationMemory:

    def __init__(self):
        self.successful_primitives = defaultdict(int)
        self.failed_primitives = defaultdict(int)
        self.node_type_success = defaultdict(int)
        self.node_type_fail = defaultdict(int)

    def record_result(self, node_type, primitive, success=True):
        if success:
            self.successful_primitives[primitive] += 1
            self.node_type_success[node_type] += 1
        else:
            self.failed_primitives[primitive] += 1
            self.node_type_fail[node_type] += 1
    def primitive_score(self, primitive):
        s = self.successful_primitives[primitive]
        f = self.failed_primitives[primitive]
        total = s + f
        return (s / total) if total else 0.5

    def node_type_score(self, node_type):
        s = self.node_type_success[node_type]
        f = self.node_type_fail[node_type]
        total = s + f
        return (s / total) if total else 0.5
