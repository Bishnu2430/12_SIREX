"""
Knowledge Graph System
Tracks entities (people, places, events) and their relationships across analyses
Provides memory and context for OSINT investigations
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import networkx as nx
from loguru import logger


class KnowledgeGraph:
    """
    Graph-based entity tracking system
    
    Stores and connects:
    - People (faces, names, identifiers)
    - Locations (GPS, addresses, landmarks)
    - Organizations (companies, groups)
    - Events (incidents, activities)
    - Devices (cameras, phones, computers)
    - Media files (images, videos, audio)
    
    Provides:
    - Entity recognition and matching
    - Relationship tracking
    - Temporal analysis
    - Graph queries and visualization
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.graph = nx.DiGraph()
        self.storage_path = Path(storage_path) if storage_path else Path("knowledge_graph.json")
        self._load_graph()
    
    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        properties: Dict[str, Any],
        source_file: Optional[str] = None
    ) -> str:
        """
        Add or update an entity in the knowledge graph
        
        Args:
            entity_id: Unique identifier
            entity_type: Person/Location/Organization/Event/Device/Media
            properties: Entity attributes
            source_file: Source media file
            
        Returns:
            Entity ID
        """
        # Check if entity already exists
        if self.graph.has_node(entity_id):
            # Update existing entity
            existing_props = self.graph.nodes[entity_id]
            existing_props.update(properties)
            existing_props['last_seen'] = datetime.now().isoformat()
            existing_props['seen_count'] = existing_props.get('seen_count', 1) + 1
            
            if source_file:
                sources = existing_props.get('sources', [])
                if source_file not in sources:
                    sources.append(source_file)
                existing_props['sources'] = sources
            
            logger.info(f"Updated entity: {entity_id}")
        else:
            # Add new entity
            self.graph.add_node(
                entity_id,
                entity_type=entity_type,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                seen_count=1,
                sources=[source_file] if source_file else [],
                **properties
            )
            logger.info(f"Added new entity: {entity_id} ({entity_type})")
        
        self._save_graph()
        return entity_id
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Add a relationship between entities
        
        Relationship types:
        - located_at: Entity at Location
        - associated_with: General association
        - member_of: Person member of Organization
        - owns: Ownership
        - captured_by: Media captured by Device
        - occurred_at: Event at Location
        - participated_in: Person in Event
        """
        if not self.graph.has_node(source_id):
            logger.warning(f"Source entity {source_id} not found")
            return
        
        if not self.graph.has_node(target_id):
            logger.warning(f"Target entity {target_id} not found")
            return
        
        edge_props = properties or {}
        edge_props.update({
            'relationship_type': relationship_type,
            'created': datetime.now().isoformat()
        })
        
        self.graph.add_edge(source_id, target_id, **edge_props)
        logger.info(f"Added relationship: {source_id} --{relationship_type}--> {target_id}")
        
        self._save_graph()
    
    def find_entity(
        self,
        entity_type: Optional[str] = None,
        **properties
    ) -> List[Dict[str, Any]]:
        """
        Find entities matching criteria
        
        Examples:
            find_entity(entity_type="Person", name="John")
            find_entity(entity_type="Location", city="New York")
        """
        results = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            # Check entity type
            if entity_type and node_data.get('entity_type') != entity_type:
                continue
            
            # Check properties
            match = True
            for key, value in properties.items():
                if key not in node_data or node_data[key] != value:
                    match = False
                    break
            
            if match:
                results.append({
                    'id': node_id,
                    **node_data
                })
        
        return results
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID"""
        if self.graph.has_node(entity_id):
            return {
                'id': entity_id,
                **self.graph.nodes[entity_id]
            }
        return None
    
    def get_relationships(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for an entity
        
        Args:
            entity_id: Entity ID
            direction: "outgoing", "incoming", or "both"
        """
        relationships = []
        
        if not self.graph.has_node(entity_id):
            return relationships
        
        # Outgoing relationships
        if direction in ["outgoing", "both"]:
            for target in self.graph.successors(entity_id):
                edge_data = self.graph.edges[entity_id, target]
                relationships.append({
                    'direction': 'outgoing',
                    'source': entity_id,
                    'target': target,
                    'target_type': self.graph.nodes[target].get('entity_type'),
                    **edge_data
                })
        
        # Incoming relationships
        if direction in ["incoming", "both"]:
            for source in self.graph.predecessors(entity_id):
                edge_data = self.graph.edges[source, entity_id]
                relationships.append({
                    'direction': 'incoming',
                    'source': source,
                    'source_type': self.graph.nodes[source].get('entity_type'),
                    'target': entity_id,
                    **edge_data
                })
        
        return relationships
    
    def get_connected_entities(
        self,
        entity_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get all entities connected to this entity up to max_depth
        
        Returns network of connected entities
        """
        if not self.graph.has_node(entity_id):
            return {}
        
        # Use BFS to find connected entities
        connected = {entity_id}
        current_level = {entity_id}
        
        for depth in range(max_depth):
            next_level = set()
            for node in current_level:
                # Add successors and predecessors
                next_level.update(self.graph.successors(node))
                next_level.update(self.graph.predecessors(node))
            
            connected.update(next_level)
            current_level = next_level
            
            if not current_level:
                break
        
        # Build subgraph
        subgraph = self.graph.subgraph(connected)
        
        # Convert to dictionary format
        result = {
            'center_entity': entity_id,
            'nodes': [],
            'edges': []
        }
        
        for node_id, node_data in subgraph.nodes(data=True):
            result['nodes'].append({
                'id': node_id,
                **node_data
            })
        
        for source, target, edge_data in subgraph.edges(data=True):
            result['edges'].append({
                'source': source,
                'target': target,
                **edge_data
            })
        
        return result
    
    def match_face(
        self,
        face_encoding: List[float],
        threshold: float = 0.6
    ) -> Optional[str]:
        """
        Match a face encoding to existing people in the graph
        
        Note: Requires face_recognition library for production use
        This is a placeholder for face matching logic
        """
        # TODO: Implement face matching using face_recognition library
        # For now, return None (no match)
        return None
    
    def match_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 1.0
    ) -> List[str]:
        """
        Find locations within radius of given coordinates
        
        Args:
            latitude: Latitude
            longitude: Longitude  
            radius_km: Search radius in kilometers
            
        Returns:
            List of matching location entity IDs
        """
        from math import radians, sin, cos, sqrt, atan2
        
        matches = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('entity_type') != 'Location':
                continue
            
            node_lat = node_data.get('latitude')
            node_lon = node_data.get('longitude')
            
            if node_lat is None or node_lon is None:
                continue
            
            # Calculate distance using Haversine formula
            R = 6371  # Earth's radius in km
            
            lat1, lon1 = radians(latitude), radians(longitude)
            lat2, lon2 = radians(node_lat), radians(node_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            if distance <= radius_km:
                matches.append(node_id)
        
        return matches
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        entity_counts = {}
        
        for node_id, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get('entity_type', 'Unknown')
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        return {
            'total_entities': self.graph.number_of_nodes(),
            'total_relationships': self.graph.number_of_edges(),
            'entity_counts': entity_counts,
            'graph_density': nx.density(self.graph),
            'storage_path': str(self.storage_path)
        }
    
    def export_for_visualization(self) -> Dict[str, Any]:
        """
        Export graph in format suitable for D3.js or other visualization
        """
        nodes = []
        links = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            nodes.append({
                'id': node_id,
                'type': node_data.get('entity_type', 'Unknown'),
                'label': node_data.get('name', node_id),
                'seen_count': node_data.get('seen_count', 1),
                **{k: v for k, v in node_data.items() 
                   if k not in ['entity_type', 'name', 'seen_count']}
            })
        
        for source, target, edge_data in self.graph.edges(data=True):
            links.append({
                'source': source,
                'target': target,
                'type': edge_data.get('relationship_type', 'related'),
                **{k: v for k, v in edge_data.items() 
                   if k != 'relationship_type'}
            })
        
        return {
            'nodes': nodes,
            'links': links
        }
    
    def _save_graph(self):
        """Save graph to disk"""
        try:
            data = {
                'nodes': [
                    {'id': node_id, **node_data}
                    for node_id, node_data in self.graph.nodes(data=True)
                ],
                'edges': [
                    {'source': source, 'target': target, **edge_data}
                    for source, target, edge_data in self.graph.edges(data=True)
                ]
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"Graph saved to {self.storage_path}")
        
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
    
    def _load_graph(self):
        """Load graph from disk"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Add nodes
                for node in data.get('nodes', []):
                    node_id = node.pop('id')
                    self.graph.add_node(node_id, **node)
                
                # Add edges
                for edge in data.get('edges', []):
                    source = edge.pop('source')
                    target = edge.pop('target')
                    self.graph.add_edge(source, target, **edge)
                
                logger.info(f"✓ Graph loaded: {self.graph.number_of_nodes()} entities, "
                          f"{self.graph.number_of_edges()} relationships")
        
        except Exception as e:
            logger.warning(f"Failed to load graph (starting fresh): {e}")
    
    def clear(self):
        """Clear all graph data"""
        self.graph.clear()
        self._save_graph()
        logger.info("Graph cleared")