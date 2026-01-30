import streamlit as st
import requests
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime

def show():
    st.title("🕸️ Intelligence Graph")
    st.markdown("Visualize entity relationships and exposure intelligence network")
    
    # Fetch graph data
    try:
        response = requests.get('http://localhost:8000/graph', timeout=5)
        
        if response.status_code == 200:
            graph_data = response.json()
            nodes = graph_data.get('nodes', [])
            links = graph_data.get('links', [])
        else:
            nodes = []
            links = []
    except:
        st.warning("⚠️ Cannot connect to API server or Neo4j is not configured")
        nodes = []
        links = []
    
    if not nodes:
        st.info("""
        📭 No graph data available yet.
        
        **To populate the graph:**
        1. Go to Media Analysis page
        2. Upload and analyze media files
        3. Ensure Neo4j is running and configured
        4. Return here to view the intelligence graph
        
        **Neo4j Setup (Optional):**
        ```bash
        docker run -d --name neo4j \\
          -p 7474:7474 -p 7687:7687 \\
          -e NEO4J_AUTH=neo4j/password \\
          neo4j:latest
        ```
        """)
        return
    
    st.success(f"✅ Graph loaded: {len(nodes)} nodes, {len(links)} relationships")
    
    # Graph controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        layout_type = st.selectbox(
            "Layout Algorithm",
            ["spring", "circular", "random", "kamada_kawai"],
            help="Choose graph layout algorithm"
        )
    
    with col2:
        node_size = st.slider("Node Size", 10, 50, 20)
    
    with col3:
        show_labels = st.checkbox("Show Labels", value=True)
    
    # Filter by entity type
    all_types = list(set([n.get('type', 'Unknown') for n in nodes]))
    selected_types = st.multiselect(
        "Filter by Entity Type",
        all_types,
        default=all_types,
        help="Select which entity types to display"
    )
    
    # Filter nodes and links
    filtered_nodes = [n for n in nodes if n.get('type') in selected_types]
    filtered_node_ids = set([n['id'] for n in filtered_nodes])
    filtered_links = [l for l in links if l['source'] in filtered_node_ids and l['target'] in filtered_node_ids]
    
    if not filtered_nodes:
        st.warning("No nodes match the selected filters")
        return
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add nodes
    for node in filtered_nodes:
        G.add_node(node['id'], type=node.get('type', 'Unknown'))
    
    # Add edges
    for link in filtered_links:
        G.add_edge(link['source'], link['target'], type=link.get('type', 'relates_to'))
    
    # Calculate layout
    if layout_type == "spring":
        pos = nx.spring_layout(G, k=0.5, iterations=50)
    elif layout_type == "circular":
        pos = nx.circular_layout(G)
    elif layout_type == "kamada_kawai":
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.random_layout(G)
    
    # Color mapping for different entity types
    color_map = {
        'Person': '#FF6B6B',
        'Location': '#4ECDC4',
        'Organization': '#45B7D1',
        'Event': '#FFA07A',
        'Exposure': '#98D8C8',
        'Entity': '#95E1D3',
        'Unknown': '#CCCCCC'
    }
    
    # Create edges for plotly
    edge_trace = []
    
    for link in filtered_links:
        source = link['source']
        target = link['target']
        
        if source in pos and target in pos:
            x0, y0 = pos[source]
            x1, y1 = pos[target]
            
            edge_trace.append(
                go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=1, color='#888'),
                    hoverinfo='text',
                    text=f"{source} → {target}<br>Type: {link.get('type', 'relates_to')}",
                    showlegend=False
                )
            )
    
    # Create nodes for plotly
    node_traces = {}
    
    for node in filtered_nodes:
        node_id = node['id']
        if node_id not in pos:
            continue
        
        node_type = node.get('type', 'Unknown')
        
        if node_type not in node_traces:
            node_traces[node_type] = {
                'x': [],
                'y': [],
                'text': [],
                'customdata': []
            }
        
        x, y = pos[node_id]
        node_traces[node_type]['x'].append(x)
        node_traces[node_type]['y'].append(y)
        node_traces[node_type]['text'].append(node_id if show_labels else '')
        
        # Hover info
        degree = G.degree(node_id)
        neighbors = list(G.neighbors(node_id))
        hover_text = f"<b>{node_id}</b><br>Type: {node_type}<br>Connections: {degree}"
        if neighbors:
            hover_text += f"<br>Connected to: {', '.join(neighbors[:5])}"
            if len(neighbors) > 5:
                hover_text += f"... and {len(neighbors)-5} more"
        
        node_traces[node_type]['customdata'].append(hover_text)
    
    # Create plotly figure
    fig = go.Figure()
    
    # Add edges
    for edge in edge_trace:
        fig.add_trace(edge)
    
    # Add nodes
    for node_type, trace_data in node_traces.items():
        fig.add_trace(
            go.Scatter(
                x=trace_data['x'],
                y=trace_data['y'],
                mode='markers+text' if show_labels else 'markers',
                marker=dict(
                    size=node_size,
                    color=color_map.get(node_type, '#CCCCCC'),
                    line=dict(width=2, color='white')
                ),
                text=trace_data['text'],
                textposition="top center",
                textfont=dict(size=10),
                hovertext=trace_data['customdata'],
                hoverinfo='text',
                name=node_type,
                showlegend=True
            )
        )
    
    # Update layout
    fig.update_layout(
        title="Intelligence Graph Network",
        titlefont_size=20,
        showlegend=True,
        hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=40),
        height=700,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        font=dict(color='white')
    )
    
    # Display graph
    st.plotly_chart(fig, use_container_width=True)
    
    # Graph statistics
    st.markdown("### 📊 Graph Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Nodes", len(filtered_nodes))
    
    with col2:
        st.metric("Total Edges", len(filtered_links))
    
    with col3:
        if G.number_of_nodes() > 0:
            density = nx.density(G)
            st.metric("Graph Density", f"{density:.3f}")
        else:
            st.metric("Graph Density", "0")
    
    with col4:
        if G.number_of_nodes() > 0:
            avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
            st.metric("Avg Connections", f"{avg_degree:.1f}")
        else:
            st.metric("Avg Connections", "0")
    
    # Node details
    with st.expander("🔍 Node Details"):
        st.markdown("#### Entity List")
        
        for node_type in sorted(all_types):
            type_nodes = [n for n in filtered_nodes if n.get('type') == node_type]
            if type_nodes:
                st.markdown(f"**{node_type}** ({len(type_nodes)} nodes)")
                for node in type_nodes:
                    node_id = node['id']
                    degree = G.degree(node_id) if node_id in G else 0
                    st.markdown(f"- `{node_id}` (Connections: {degree})")
    
    # Relationship details
    with st.expander("🔗 Relationship Details"):
        st.markdown("#### Edge List")
        
        relationship_types = {}
        for link in filtered_links:
            rel_type = link.get('type', 'relates_to')
            if rel_type not in relationship_types:
                relationship_types[rel_type] = []
            relationship_types[rel_type].append(f"{link['source']} → {link['target']}")
        
        for rel_type, rels in sorted(relationship_types.items()):
            st.markdown(f"**{rel_type}** ({len(rels)} relationships)")
            for rel in rels[:10]:  # Show first 10
                st.markdown(f"- {rel}")
            if len(rels) > 10:
                st.markdown(f"... and {len(rels)-10} more")
    
    # Export
    with st.expander("💾 Export Graph Data"):
        import json
        
        export_data = {
            "nodes": filtered_nodes,
            "links": filtered_links,
            "statistics": {
                "node_count": len(filtered_nodes),
                "edge_count": len(filtered_links),
                "density": nx.density(G) if G.number_of_nodes() > 0 else 0,
                "exported_at": datetime.now().isoformat()
            }
        }
        
        json_data = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="📥 Download Graph (JSON)",
            data=json_data,
            file_name="intelligence_graph.json",
            mime="application/json"
        )
    
    # Information
    with st.expander("ℹ️ About Intelligence Graphs"):
        st.markdown("""
        ### What is an Intelligence Graph?
        
        An intelligence graph represents relationships between entities discovered during OSINT analysis:
        
        - **Nodes**: Entities (Persons, Locations, Organizations, Events, Exposures)
        - **Edges**: Relationships between entities (e.g., "Person AT_LOCATION", "Person AFFILIATED_WITH Organization")
        
        ### Node Types
        
        - 🔴 **Person**: Individuals detected via facial recognition
        - 🔵 **Location**: Geographical places identified
        - 🟣 **Organization**: Companies, institutions detected
        - 🟠 **Event**: Activities or gatherings
        - 🟢 **Exposure**: Privacy/security exposures
        
        ### Graph Metrics
        
        - **Density**: How interconnected the graph is (0-1)
        - **Avg Connections**: Average number of relationships per entity
        - **Degree**: Number of connections for a specific node
        
        ### Use Cases
        
        - Pattern discovery across multiple analyses
        - Entity correlation and profiling
        - Exposure impact assessment
        - Investigation support
        """)