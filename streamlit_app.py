"""
Professional OSINT Analysis Platform
Minimal, clean interface for media analysis and intelligence extraction
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="OSINT Analysis Platform",
    page_icon="⬢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #4CAF50;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1a1d24;
    }
    
    .streamlit-expanderHeader {
        background-color: #1a1d24;
        border: 1px solid #2d3139;
        border-radius: 4px;
    }
    
    [data-testid="stContainer"] {
        border: 1px solid #2d3139;
        border-radius: 4px;
        background-color: #1a1d24;
    }
    
    .stButton button {
        background-color: #2d3139;
        color: white;
        border: 1px solid #3d4149;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton button:hover {
        background-color: #3d4149;
        border-color: #4d5159;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    code {
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Session state initialization
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'vision_insights' not in st.session_state:
    st.session_state.vision_insights = None

# Sidebar navigation
with st.sidebar:
    st.markdown("### OSINT Platform")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["Media Analysis", "Observability", "Knowledge Graph"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.caption("Advanced Intelligence Extraction")


# ============================================================================
# PAGE 1: MEDIA ANALYSIS
# ============================================================================
if page == "Media Analysis":
    st.title("Media Analysis")
    st.caption("Upload and analyze media files for OSINT intelligence")
    
    uploaded_file = st.file_uploader(
        "Select media file",
        type=['jpg', 'jpeg', 'png', 'mp4', 'mov', 'avi', 'wav', 'mp3'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(f"File: {uploaded_file.name}")
        with col2:
            st.text(f"Size: {uploaded_file.size/1024:.2f} KB")
        
        # Media preview
        if uploaded_file.type.startswith('image'):
            st.image(uploaded_file, width=600)
        elif uploaded_file.type.startswith('video'):
            st.video(uploaded_file)
        elif uploaded_file.type.startswith('audio'):
            st.audio(uploaded_file)
        
        if st.button("Analyze"):
            with st.spinner("Processing..."):
                try:
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_BASE_URL}/api/analyze", files=files, timeout=300)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.analysis_result = result
                        st.session_state.session_id = result.get('analysis_id')
                        st.session_state.vision_insights = None
                        st.success("Analysis complete")
                        st.rerun()
                    else:
                        st.error(f"Analysis failed: HTTP {response.status_code}")
                        st.code(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        
        st.markdown("---")
        st.markdown("### Analysis Results")
        
        metadata = result.get('metadata', {})
        intelligence = result.get('llm_intelligence', {})
        audio = result.get('audio_analysis') or {}  # Handle None
        vision = result.get('vision_analysis') or {}  # Handle None
        processing_time = result.get('processing_time', 0)
        
        st.caption(f"Completed in {processing_time:.2f}s")
        
        # Debug: Show what we got
        if not intelligence:
            st.warning("No intelligence data received from analysis")
            with st.expander("Debug: View raw result"):
                st.json(result)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            entities_count = len(intelligence.get('entities', []))
            st.metric("Entities", entities_count)
        with col2:
            exposures_count = len(intelligence.get('exposures', []))
            st.metric("Exposures", exposures_count)
        with col3:
            relationships_count = len(intelligence.get('relationships', []))
            st.metric("Relationships", relationships_count)
        with col4:
            file_size = metadata.get('file', {}).get('size_mb', 0) if metadata else 0
            st.metric("File Size", f"{file_size:.2f} MB")
        
        # Executive Summary
        if intelligence.get('executive_summary'):
            st.markdown("### Executive Summary")
            with st.container(border=True):
                st.markdown(intelligence['executive_summary'])
        
        # Narrative Report - Intelligence in Readable Format
        if intelligence.get('narrative_report'):
            st.markdown("### Intelligence Report")
            with st.container(border=True):
                st.markdown(intelligence['narrative_report'])
        
        # Audio Transcription (if available)
        if audio and audio.get('transcription'):
            st.markdown("### Audio Transcription")
            with st.container(border=True):
                transcriptions = audio['transcription']
                
                # Check for Google transcription
                if 'google' in transcriptions:
                    google_trans = transcriptions['google']
                    if 'text' in google_trans:
                        st.write(google_trans['text'])
                        st.caption(f"Engine: {google_trans.get('engine', 'Unknown')} | Confidence: {google_trans.get('confidence', 'N/A')}")
                    elif 'error' in google_trans:
                        st.info(google_trans['error'])
                
                # Show other transcriptions
                if 'sphinx' in transcriptions and 'text' in transcriptions['sphinx']:
                    with st.expander("Alternative transcription (Sphinx)"):
                        st.write(transcriptions['sphinx']['text'])
                
                # Full transcription data
                with st.expander("View complete transcription data"):
                    st.json(transcriptions)
        
        # Visual Intelligence (formatted)
        visual_intel = intelligence.get('visual_intelligence', {})
        if visual_intel:
            st.markdown("### Visual Intelligence")
            
            # People detected
            people = visual_intel.get('people', [])
            if people:
                with st.expander(f"People Detected ({len(people)})"):
                    for person in people:
                        st.markdown(f"**{person.get('id', 'Unknown')}**")
                        st.write(person.get('description', 'No description'))
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if person.get('estimated_age_range'):
                                st.caption(f"Age: {person['estimated_age_range']}")
                        with col2:
                            if person.get('gender'):
                                st.caption(f"Gender: {person['gender']}")
                        with col3:
                            if person.get('confidence'):
                                st.progress(person['confidence'], text=f"{person['confidence']:.0%}")
                        
                        if person.get('clothing'):
                            st.write(f"Clothing: {person['clothing']}")
                        if person.get('distinctive_features'):
                            st.write(f"Features: {', '.join(person['distinctive_features'])}")
                        
                        st.markdown("---")
            
            # Objects detected
            objects = visual_intel.get('objects', [])
            if objects:
                with st.expander(f"Objects Detected ({len(objects)})"):
                    for obj in objects:
                        st.markdown(f"**{obj.get('name', 'Unknown')}**")
                        st.write(obj.get('description', 'No description'))
                        if obj.get('brand'):
                            st.caption(f"Brand: {obj['brand']}")
                        if obj.get('significance'):
                            st.info(obj['significance'])
                        if obj.get('confidence'):
                            st.progress(obj['confidence'], text=f"{obj['confidence']:.0%}")
                        st.markdown("---")
            
            # Environment analysis
            environment = visual_intel.get('environment', {})
            if environment:
                with st.expander("Environment Analysis"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if environment.get('setting'):
                            st.metric("Setting", environment['setting'])
                        if environment.get('indoor_outdoor'):
                            st.metric("Location Type", environment['indoor_outdoor'])
                    with col2:
                        if environment.get('lighting'):
                            st.metric("Lighting", environment['lighting'])
                        if environment.get('weather'):
                            st.metric("Weather", environment['weather'])
                    
                    if environment.get('description'):
                        st.write(environment['description'])
        
        # Entities
        entities = intelligence.get('entities', [])
        if entities:
            st.markdown("### Identified Entities")
            with st.expander(f"View {len(entities)} entities with confidence scores"):
                for entity in entities:
                    entity_type = entity.get('type', 'Unknown')
                    entity_name = entity.get('name', entity.get('value', 'N/A'))
                    confidence = entity.get('confidence', 0)
                    
                    st.markdown(f"**{entity_type}**: {entity_name}")
                    if confidence:
                        st.progress(confidence, text=f"Confidence: {confidence:.0%}")
                    
                    # Show all additional fields
                    with st.expander("Complete entity data"):
                        st.json(entity)
                    st.markdown("---")
        
        # Exposures
        exposures = intelligence.get('exposures', [])
        if exposures:
            st.markdown("### Security Exposures")
            
            for idx, exp in enumerate(exposures, 1):
                severity = exp.get('severity', 'UNKNOWN').upper()
                severity_color = {
                    'CRITICAL': '#ef4444',
                    'HIGH': '#f97316',
                    'MEDIUM': '#eab308',
                    'LOW': '#22c55e'
                }.get(severity, '#6b7280')
                
                exp_type = exp.get('type', exp.get('exposure_type', 'Unknown'))
                
                with st.expander(f"{exp_type} - {severity}"):
                    st.markdown(f"**Severity:** <span style='color:{severity_color}'>{severity}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Category:** {exp.get('category', 'N/A')}")
                    st.write(exp.get('description', exp.get('finding', 'N/A')))
                    
                    if exp.get('attack_scenarios'):
                        st.markdown("**Attack Scenarios:**")
                        for scenario in exp['attack_scenarios']:
                            st.markdown(f"- {scenario}")
                    
                    if exp.get('recommendations'):
                        st.markdown("**Recommended Actions:**")
                        for rec in exp['recommendations']:
                            st.markdown(f"- {rec}")
                    
                    # Complete data
                    with st.expander("Complete exposure data"):
                        st.json(exp)
        
        # Geolocation
        geolocation = intelligence.get('geolocation', {})
        metadata_loc = metadata.get('location', {})
        
        if geolocation or metadata_loc:
            st.markdown("### Geolocation Intelligence")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if geolocation:
                    st.markdown("**Estimated Location**")
                    location = geolocation.get('estimated_location', geolocation.get('location', 'Unknown'))
                    confidence = geolocation.get('confidence', 0)
                    st.write(location)
                    if confidence:
                        st.progress(confidence, text=f"Confidence: {confidence:.0%}")
                    
                    if geolocation.get('reasoning'):
                        with st.expander("Geolocation reasoning"):
                            st.write(geolocation['reasoning'])
                    
                    # Show all geolocation data
                    with st.expander("Complete geolocation data"):
                        st.json(geolocation)
            
            with col2:
                if metadata_loc and metadata_loc.get('latitude'):
                    st.markdown("**GPS Coordinates (EXIF)**")
                    st.write(f"Latitude: {metadata_loc['latitude']:.6f}")
                    st.write(f"Longitude: {metadata_loc['longitude']:.6f}")
                    if metadata_loc.get('altitude'):
                        st.write(f"Altitude: {metadata_loc['altitude']}m")
        
        # Audio Properties (if audio file)
        if audio and (audio.get('acoustic_features') or audio.get('speech_characteristics')):
            st.markdown("### Audio Intelligence")
            
            with st.expander("View audio analysis"):
                if audio.get('acoustic_features'):
                    st.markdown("**Acoustic Features**")
                    st.json(audio['acoustic_features'])
                
                if audio.get('speech_characteristics'):
                    st.markdown("**Speech Characteristics**")
                    st.json(audio['speech_characteristics'])
                
                if audio.get('environmental_analysis'):
                    st.markdown("**Environmental Analysis**")
                    st.json(audio['environmental_analysis'])


# ============================================================================
# PAGE 2: OBSERVABILITY
# ============================================================================
elif page == "Observability":
    st.title("Analysis Observability")
    st.caption("Analysis pipeline, reasoning traces, and AI-powered insights")
    
    if not st.session_state.analysis_result:
        st.info("No analysis data available. Please analyze a media file first.")
    else:
        result = st.session_state.analysis_result
        
        # Analysis Pipeline
        st.markdown("### Analysis Pipeline")
        steps = result.get('analysis_steps', [])
        if steps:
            for step in steps:
                st.text(f"✓ {step.get('step', 'Unknown')} - {step.get('timestamp', '')}")
        
        # Intelligence Reasoning Trace
        st.markdown("### Intelligence Reasoning")
        st.caption("Step-by-step analysis and decision-making process")
        
        reasoning_trace = result.get('reasoning_trace', {})
        
        if reasoning_trace:
            with st.container(border=True):
                if isinstance(reasoning_trace, dict):
                    model = reasoning_trace.get('model', 'Unknown')
                    st.caption(f"Analysis Engine: {model}")
                    st.markdown("---")
                    
                    if reasoning_trace.get('observations'):
                        st.markdown("**Observations**")
                        st.markdown("*Initial data analysis and pattern recognition*")
                        st.write(reasoning_trace['observations'])
                        st.markdown("---")
                    
                    if reasoning_trace.get('deductions'):
                        st.markdown("**Deductions**")
                        st.markdown("*Logical conclusions from observations*")
                        st.write(reasoning_trace['deductions'])
                        st.markdown("---")
                    
                    if reasoning_trace.get('hypotheses'):
                        st.markdown("**Hypotheses**")
                        st.markdown("*Possible explanations and scenarios*")
                        st.write(reasoning_trace['hypotheses'])
                else:
                    st.write(reasoning_trace)
        
        # AI-Powered Vision Insights
        vision_data = result.get('vision_analysis', {})
        
        if vision_data:
            st.markdown("### AI-Powered Visual Intelligence")
            st.caption("Deep reasoning from computer vision data")
            
            if st.session_state.vision_insights:
                insights = st.session_state.vision_insights.get('insights', '')
                model = st.session_state.vision_insights.get('model', 'Unknown')
                
                st.caption(f"Generated by {model}")
                
                with st.container(border=True):
                    st.markdown(insights)
                
                if st.button("Regenerate Insights"):
                    st.session_state.vision_insights = None
                    st.rerun()
            else:
                if st.button("Generate Deep Visual Intelligence"):
                    with st.spinner("Analyzing visual patterns..."):
                        try:
                            resp = requests.post(
                                f"{API_BASE_URL}/api/insights/vision",
                                json={'vision_data': vision_data, 'context': 'OSINT Investigation'},
                                timeout=30
                            )
                            if resp.status_code == 200:
                                st.session_state.vision_insights = resp.json()
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        # Complete Data
        st.markdown("### Complete Analysis Data")
        st.caption("All extracted data with confidence scores")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Metadata",
            "Visual Data",
            "Audio Data",
            "Full Response"
        ])
        
        with tab1:
            st.json(result.get('metadata', {}))
        
        with tab2:
            vision = result.get('vision_analysis', {})
            if vision.get('google_vision'):
                gv = vision['google_vision']
                
                for key, value in gv.items():
                    if value:
                        with st.expander(f"{key.replace('_', ' ').title()} ({len(value) if isinstance(value, list) else 'data'})"):
                            st.json(value)
            else:
                st.json(vision)
        
        with tab3:
            st.json(result.get('audio_analysis', {}))
        
        with tab4:
            st.json(result)


# ============================================================================
# PAGE 3: KNOWLEDGE GRAPH
# ============================================================================
elif page == "Knowledge Graph":
    st.title("Knowledge Graph")
    st.caption("Entity relationships and connections")
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Refresh"):
            st.rerun()
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/graph/statistics", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Entities", stats.get('total_entities', 0))
            with col2:
                st.metric("Relationships", stats.get('total_relationships', 0))
            with col3:
                st.metric("Density", f"{stats.get('graph_density', 0):.3f}")
            
            entity_counts = stats.get('entity_counts', {})
            if entity_counts:
                st.markdown("### Entity Distribution")
                for etype, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
                    st.text(f"{etype}: {count}")
        
        response = requests.get(f"{API_BASE_URL}/api/graph/export", timeout=5)
        if response.status_code == 200:
            graph_data = response.json()
            nodes = graph_data.get('nodes', [])
            edges = graph_data.get('edges', graph_data.get('links', []))
            
            if nodes and edges:
                st.markdown("### Graph Visualization")
                
                import math
                node_ids = {node['id']: idx for idx, node in enumerate(nodes)}
                
                edge_x, edge_y = [], []
                for edge in edges:
                    src = edge.get('source', edge.get('from'))
                    tgt = edge.get('target', edge.get('to'))
                    src_idx = node_ids.get(src)
                    tgt_idx = node_ids.get(tgt)
                    
                    if src_idx is not None and tgt_idx is not None:
                        ang_s = 2 * math.pi * src_idx / len(nodes)
                        ang_t = 2 * math.pi * tgt_idx / len(nodes)
                        edge_x.extend([math.cos(ang_s), math.cos(ang_t), None])
                        edge_y.extend([math.sin(ang_s), math.sin(ang_t), None])
                
                node_x, node_y, node_text, node_colors = [], [], [], []
                type_colors = {
                    'PERSON': '#ff6b6b',
                    'LOCATION': '#4ecdc4',
                    'ORGANIZATION': '#45b7d1',
                    'EVENT': '#f9ca24',
                    'DEVICE': '#6c5ce7',
                    'MEDIA': '#95a5a6'
                }
                
                for idx, node in enumerate(nodes):
                    ang = 2 * math.pi * idx / len(nodes)
                    node_x.append(math.cos(ang))
                    node_y.append(math.sin(ang))
                    
                    node_type = node.get('type', node.get('entity_type', 'Unknown'))
                    node_label = node.get('label', node.get('name', node.get('id', '')))
                    node_text.append(f"{node_type}: {node_label}")
                    node_colors.append(type_colors.get(node_type.upper(), '#4CAF50'))
                
                fig = go.Figure(data=[
                    go.Scatter(
                        x=edge_x, y=edge_y,
                        mode='lines',
                        line=dict(width=1, color='#3d4149'),
                        hoverinfo='none',
                        showlegend=False
                    ),
                    go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers+text',
                        hovertext=node_text,
                        hoverinfo='text',
                        marker=dict(size=12, color=node_colors, line=dict(width=1, color='white')),
                        text=[node.get('type', '')[:1].upper() for node in nodes],
                        textfont=dict(size=8, color='white'),
                        textposition='middle center',
                        showlegend=False
                    )
                ])
                
                fig.update_layout(
                    showlegend=False,
                    hovermode='closest',
                    height=500,
                    margin=dict(l=0, r=0, t=0, b=0),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("View all entities"):
                    st.json(nodes)
                
                with st.expander("View all relationships"):
                    st.json(edges)
            else:
                st.info("No graph data. Analyze media files to populate.")
                
    except Exception as e:
        st.error(f"Connection error: {e}")
        st.info("Ensure backend is running: `uvicorn app.main:app --reload`")