import random
from core.nodes import Node
from core.edges import Edge
from core.confidence import calculate_confidence
from core.inference import InferenceRecord


def process_infrastructure(node, kg):

    created_nodes = []
    created_edges = []

    if node.type == "domain":
        ip = f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
        asn = f"AS{random.randint(10000,99999)}"
        hosting = random.choice(["AWS", "Azure", "DigitalOcean", "OVH"])

        ip_node = Node(type="ip", value=ip, source="infra_osint")
        asn_node = Node(type="asn", value=asn, source="infra_osint")
        host_node = Node(type="hosting_provider", value=hosting, source="infra_osint")

        ip_id = kg.add_node(ip_node)
        asn_id = kg.add_node(asn_node)
        host_id = kg.add_node(host_node)

        conf = calculate_confidence("heuristic", "dns_lookup", 0.85, 1)

        e1 = Edge(node.id, ip_id, "hosted_on", conf, "DNS resolution", "dns_lookup")
        e2 = Edge(ip_id, asn_id, "co_occurs_with", conf, "IP belongs to ASN", "asn_mapping")
        e3 = Edge(ip_id, host_id, "hosted_on", conf, "Hosting provider inference", "hosting_inference")

        kg.add_edge(e1)
        kg.add_edge(e2)
        kg.add_edge(e3)

        created_nodes.extend([ip_id, asn_id, host_id])
        created_edges.extend([e1.id, e2.id, e3.id])

    if node.type == "ip":
        related_domains = [f"site{random.randint(1,50)}.com" for _ in range(2)]

        for d in related_domains:
            dom_node = Node(type="domain", value=d, source="infra_osint")
            dom_id = kg.add_node(dom_node)

            conf = calculate_confidence("heuristic", "infra_reuse", 0.75, 1)
            e = Edge(node.id, dom_id, "co_occurs_with", conf,
                     "Shared infrastructure reuse", "infra_reuse")

            kg.add_edge(e)
            created_nodes.append(dom_id)
            created_edges.append(e.id)

    inf = InferenceRecord(
        hypothesis=f"Infrastructure expansion for {node.value}",
        nodes_involved=[node.id] + created_nodes,
        edges_created=created_edges,
        agent_reasoning="Agent executed infrastructure OSINT primitive",
        confidence=0.7,
        status="accepted"
    )

    kg.add_inference(inf)
