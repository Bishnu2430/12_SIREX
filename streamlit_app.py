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
API_URL = API_BASE_URL  # Alias for compatibility

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
        ["Media Analysis", "GitHub OSINT", "Twitter OSINT", "IP OSINT", "Observability", "Knowledge Graph"],
        label_visibility="collapsed"
    )
    
    # SpiderFoot link with inline logo
    import os
    import base64
    logo_path = os.path.join(os.path.dirname(__file__), "spiderfoot.png")
    
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
        <a href="http://localhost:5001" target="_blank" style="
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            text-decoration: none;
            color: #fff;
            font-weight: 500;
        ">
            <img src="data:image/png;base64,{logo_data}" width="24" height="24" />
            <span>SpiderFoot</span>
        </a>
        """, unsafe_allow_html=True)
    
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
        
        # Get exposure report data
        exposure_report = result.get('exposure_report', {})
        exposure_summary = exposure_report.get('summary', {})
        detected_exposures = exposure_report.get('exposures', [])
        
        with col1:
            entities_count = len(intelligence.get('entities', []))
            st.metric("Entities", entities_count)
        with col2:
            # Priority: Show rule-based exposures count
            total_exposures = exposure_summary.get('total_count', 0)
            st.metric("🔍 Exposures Detected", total_exposures, 
                     delta=f"{exposure_summary.get('by_severity', {}).get('critical', 0)} critical" if exposure_summary.get('by_severity', {}).get('critical', 0) > 0 else None,
                     delta_color="inverse")
        with col3:
            relationships_count = len(intelligence.get('relationships', []))
            st.metric("Relationships", relationships_count)
        with col4:
            file_size = metadata.get('file', {}).get('size_mb', 0) if metadata else 0
            st.metric("File Size", f"{file_size:.2f} MB")
        
        # ============================================================================
        # PRIMARY: EXPOSURE-CENTRIC ANALYSIS (Rule-Based Detection)
        # ============================================================================
        if detected_exposures:
            st.markdown("---")
            st.markdown("## 🔍 Exposure Analysis")
            st.caption("Rule-based detection of unintentional information leaks")
            
            # Severity summary badges
            severity_counts = exposure_summary.get('by_severity', {})
            if sum(severity_counts.values()) > 0:
                badge_cols = st.columns(5)
                severity_config = {
                    'critical': ('🔴', '#ef4444', 'CRITICAL'),
                    'high': ('🟠', '#f97316', 'HIGH'),
                    'medium': ('🟡', '#eab308', 'MEDIUM'),
                    'low': ('🟢', '#22c55e', 'LOW'),
                    'info': ('🔵', '#3b82f6', 'INFO')
                }
                
                for idx, (sev_key, (emoji, color, label)) in enumerate(severity_config.items()):
                    count = severity_counts.get(sev_key, 0)
                    if count > 0:
                        with badge_cols[idx]:
                            st.markdown(f"""
                            <div style='background: {color}15; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid {color}'>
                                <div style='font-size: 24px;'>{emoji}</div>
                                <div style='font-size: 20px; font-weight: bold; color: {color}'>{count}</div>
                                <div style='font-size: 12px; color: {color}'>{label}</div>
                            </div>
                            """, unsafe_allow_html=True)
            
            st.markdown("")  # Spacing
            
            # Display each exposure as a card
            for exp_data in detected_exposures:
                severity = exp_data.get('severity', 'info')
                category = exp_data.get('category', 'unknown')
                title = exp_data.get('title', 'Exposure Detected')
                description = exp_data.get('description', '')
                evidence = exp_data.get('evidence', {})
                risk = exp_data.get('risk_explanation', '')
                recommendations = exp_data.get('recommendations', [])
                confidence = exp_data.get('confidence', 1.0)
                
                # Color coding by severity
                severity_colors = {
                    'critical': ('#ef4444', '🔴'),
                    'high': ('#f97316', '🟠'),
                    'medium': ('#eab308', '🟡'),
                    'low': ('#22c55e', '🟢'),
                    'info': ('#3b82f6', '🔵')
                }
                color, emoji = severity_colors.get(severity.lower(), ('#6b7280', '⚪'))
                
                # Exposure card
                st.markdown(f"""
                <div style='border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background: {color}08; border-radius: 5px;'>
                    <h4 style='margin: 0; color: {color};'>{emoji} {title}</h4>
                    <p style='margin: 5px 0; color: #666;'><strong>Category:</strong> {category.upper()} | <strong>Severity:</strong> {severity.upper()} | <strong>Confidence:</strong> {confidence*100:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.container(border=True):
                    # Description
                    st.markdown(f"**Description:** {description}")
                    
                    # Evidence
                    if evidence:
                        st.markdown("**Evidence:**")
                        for key, value in evidence.items():
                            # Mask sensitive data
                            if isinstance(value, str) and len(value) > 50:
                                value = value[:20] + "..." + value[-10:]
                            st.markdown(f"- `{key}`: {value}")
                    
                    # Risk explanation
                    if risk:
                        st.warning(f"**Risk:** {risk}")
                    
                    # Recommendations
                    if recommendations:
                        st.markdown("**Recommended Actions:**")
                        for rec in recommendations:
                            st.markdown(f"- ✅ {rec}")
                
                st.markdown("")  # Spacing
        
        # ============================================================================
        # OPTIONAL: LLM Intelligence Analysis (if available)
        # ============================================================================
        if intelligence and (intelligence.get('narrative_report') or intelligence.get('executive_summary')):
            with st.expander("📊 Additional Intelligence Analysis (LLM-generated)", expanded=False):
                st.caption("Optional AI-generated insights - may be unavailable if API fails")
                
                # Executive Summary
                if intelligence.get('executive_summary'):
                    st.markdown("### Executive Summary")
                    with st.container(border=True):
                        st.markdown(intelligence['executive_summary'])
                
                # Narrative Report
                if intelligence.get('narrative_report'):
                    st.markdown("### Intelligence Report")
                    with st.container(border=True):
                        st.markdown(intelligence['narrative_report'])
        
        
        # Audio Transcription (if available)
        if audio and audio.get('transcription'):
            st.markdown("### 🎤 Audio Transcription")
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

# ============================================================================
# GitHub OSINT PAGE
# ============================================================================
elif page == "GitHub OSINT":
    st.title("GitHub OSINT Analysis")
    st.caption("Analyze GitHub profiles for OSINT intelligence")
    
    username = st.text_input("GitHub Username", placeholder="Enter username...")
    
    if st.button("Analyze", type="primary", use_container_width=True):
        if not username:
            st.error("Please enter a username")
        else:
            with st.spinner(f"Analyzing GitHub user: {username}..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/github/analyze",
                        data={"username": username}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Profile Overview
                        st.markdown("### Profile Overview")
                        profile = result.get("profile", {})
                        basic_info = profile.get("basic_info", {})
                        metrics = profile.get("account_metrics", {})
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Followers", metrics.get("followers", 0))
                        with col2:
                            st.metric("Following", metrics.get("following", 0))
                        with col3:
                            st.metric("Public Repos", metrics.get("public_repos", 0))
                        with col4:
                            st.metric("Gists", metrics.get("public_gists", 0))
                        
                        # Basic Info
                        if basic_info.get("name") or basic_info.get("bio"):
                            with st.expander("👤 Profile Information", expanded=True):
                                if basic_info.get("name"):
                                    st.markdown(f"**Name:** {basic_info['name']}")
                                if basic_info.get("bio"):
                                    st.markdown(f"**Bio:** {basic_info['bio']}")
                                if basic_info.get("location"):
                                    st.markdown(f"**Location:** {basic_info['location']}")
                                if basic_info.get("company"):
                                    st.markdown(f"**Company:** {basic_info['company']}")
                                if basic_info.get("email"):
                                    st.markdown(f"**Email:** {basic_info['email']}")
                                if basic_info.get("blog"):
                                    st.markdown(f"**Blog:** {basic_info['blog']}")
                                if basic_info.get("twitter_username"):
                                    st.markdown(f"**Twitter:** @{basic_info['twitter_username']}")
                        
                        # Intelligence Summary
                        summary = result.get("intelligence_summary", {})
                        if summary:
                            st.markdown("### Intelligence Summary")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**User Type:** {summary.get('user_type', 'N/A')}")
                                st.markdown(f"**Primary Language:** {summary.get('primary_language', 'N/A')}")
                                st.markdown(f"**Activity Level:** {summary.get('activity_level', 'N/A')}")
                            
                            with col2:
                                st.markdown(f"**Total Stars:** {summary.get('total_stars', 0)}")
                                st.markdown(f"**Network Size:** {summary.get('network_size', 0)}")
                                st.markdown(f"**Exposure Risk:** {summary.get('exposure_risk', 'N/A')}")
                            
                            if summary.get('key_findings'):
                                st.markdown("**Key Findings:**")
                                for finding in summary['key_findings']:
                                    st.markdown(f"- {finding}")
                        
                        # Tech Stack
                        repos = result.get("repositories", {})
                        languages = repos.get("statistics", {}).get("languages", {})
                        if languages:
                            st.markdown("### Technology Stack")
                            
                            # Create language distribution chart
                            import plotly.express as px
                            lang_df = pd.DataFrame(list(languages.items()), columns=['Language', 'Count'])
                            lang_df = lang_df.sort_values('Count', ascending=False).head(10)
                            
                            fig = px.bar(lang_df, x='Language', y='Count', title='Top Programming Languages')
                            fig.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font_color='#ffffff'
                           )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Repositories
                        repo_list = repos.get("repositories", [])
                        if repo_list:
                            st.markdown("### Top Repositories")
                            
                            # Sort by stars
                            sorted_repos = sorted(repo_list, key=lambda x: x.get('stars', 0), reverse=True)[:10]
                            
                            for repo in sorted_repos:
                                with st.expander(f"📦 {repo['name']} ⭐ {repo.get('stars', 0)}"):
                                    if repo.get('description'):
                                        st.markdown(f"**Description:** {repo['description']}")
                                    st.markdown(f"**Language:** {repo.get('language', 'N/A')}")
                                    st.markdown(f"**Forks:** {repo.get('forks', 0)} | **Watchers:** {repo.get('watchers', 0)}")
                                    st.markdown(f"**URL:** {repo.get('url', '')}")
                                    if repo.get('topics'):
                                        st.markdown(f"**Topics:** {', '.join(repo['topics'])}")
                        
                        # Activity Patterns
                        activity = result.get("activity", {})
                        if activity.get("hourly_distribution"):
                            st.markdown("### Activity Patterns")
                            
                            hourly = activity['hourly_distribution']
                            hours = list(range(24))
                            
                            fig = go.Figure(data=go.Bar(x=hours, y=hourly))
                            fig.update_layout(
                                title="Activity Distribution by Hour",
                                xaxis_title="Hour of Day",
                                yaxis_title="Activity Count",
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font_color='#ffffff'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Network
                        network = result.get("network", {})
                        if network.get("organizations"):
                            st.markdown("### Organizations")
                            cols = st.columns(min(len(network["organizations"]), 4))
                            for idx, org in enumerate(network["organizations"][:8]):
                                with cols[idx % 4]:
                                    st.markdown(f"**{org['name']}**")
                        
                        # Exposures
                        exposures = result.get("exposures", [])
                        if exposures:
                            st.markdown("### Security Exposures")
                            
                            for exp in exposures:
                                severity = exp.get('severity', 'UNKNOWN')
                                color = {
                                    'CRITICAL': '#ef4444',
                                    'HIGH': '#f97316',
                                    'MEDIUM': '#eab308',
                                    'LOW': '#22c55e'
                                }.get(severity, '#6b7280')
                                
                                with st.expander(f"{exp.get('type', 'Exposure')} - {severity}"):
                                    st.markdown(f"**Severity:** <span style='color:{color}'>{severity}</span>", unsafe_allow_html=True)
                                    st.write(exp.get('description', 'N/A'))
                                    if exp.get('value'):
                                        st.markdown(f"**Value:** `{exp['value']}`")
                                    if exp.get('recommendation'):
                                        st.info(exp['recommendation'])
                        
                        # Raw data
                        with st.expander("📄 View raw data"):
                            st.json(result)
                        
                    elif response.status_code == 503:
                        st.error("GitHub analyzer not configured. Please add GITHUB_ACCESS_TOKEN to .env file")
                    else:
                        st.error(f"Analysis failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    st.caption("GitHub OSINT powered by GitHub API")


# ============================================================================
# Twitter OSINT PAGE
# ============================================================================
elif page == "Twitter OSINT":
    st.title("Twitter/X OSINT Analysis")
    st.caption("Analyze Twitter profiles for OSINT intelligence")
    
    username = st.text_input("Twitter Username", placeholder="Enter username (without @)...")
    
    if st.button("Analyze", type="primary", use_container_width=True):
        if not username:
            st.error("Please enter a username")
        else:
            with st.spinner(f"Analyzing Twitter user: @{username}..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/twitter/analyze",
                        data={"username": username}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Profile Overview
                        st.markdown("### Profile Overview")
                        profile = result.get("profile", {})
                        basic_info = profile.get("basic_info", {})
                        metrics = profile.get("account_metrics", {})
                        status = profile.get("account_status", {})
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Followers", f"{metrics.get('followers', 0):,}")
                        with col2:
                            st.metric("Following", f"{metrics.get('following', 0):,}")
                        with col3:
                            st.metric("Tweets", f"{metrics.get('tweets', 0):,}")
                        with col4:
                            verified = "✓" if status.get("verified") else "✗"
                            st.metric("Verified", verified)
                        
                        # Basic Info
                        with st.expander("👤 Profile Information", expanded=True):
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                if basic_info.get("profile_image"):
                                    st.image(basic_info["profile_image"], width=150)
                            
                            with col2:
                                if basic_info.get("name"):
                                    st.markdown(f"**Name:** {basic_info['name']}")
                                st.markdown(f"**Username:** @{basic_info.get('username')}")
                                if basic_info.get("bio"):
                                    st.markdown(f"**Bio:** {basic_info['bio']}")
                                if basic_info.get("location"):
                                    st.markdown(f"**Location:** {basic_info['location']}")
                                if basic_info.get("url"):
                                    st.markdown(f"**Website:** {basic_info['url']}")
                                if status.get("protected"):
                                    st.warning("🔒 Protected Account")
                        
                        # Intelligence Summary
                        summary = result.get("intelligence_summary", {})
                        if summary:
                            st.markdown("### Intelligence Summary")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**Account Type:** {summary.get('account_type', 'N/A')}")
                                st.markdown(f"**Activity Level:** {summary.get('activity_level', 'N/A')}")
                                st.markdown(f"**Content Focus:** {summary.get('content_focus', 'N/A')}")
                            
                            with col2:
                                st.markdown(f"**Engagement Rate:** {summary.get('engagement_rate', 'N/A')}")
                                st.markdown(f"**Follower Ratio:** {summary.get('follower_ratio', 0)}")
                                st.markdown(f"**Exposure Risk:** {summary.get('exposure_risk', 'N/A')}")
                            
                            if summary.get('key_findings'):
                                st.markdown("**Key Findings:**")
                                for finding in summary['key_findings']:
                                    st.markdown(f"- {finding}")
                        
                        # Tweet Analysis
                        tweets = result.get("tweets", {})
                        if tweets.get("total_analyzed", 0) > 0:
                            st.markdown("### Tweet Activity")
                            
                            # Activity Patterns
                            patterns = tweets.get("patterns", {})
                            if patterns.get("hourly_distribution"):
                                hourly = patterns['hourly_distribution']
                                hours = list(range(24))
                                
                                fig = go.Figure(data=go.Bar(x=hours, y=hourly))
                                fig.update_layout(
                                    title="Tweet Activity by Hour",
                                    xaxis_title="Hour of Day (24h)",
                                    yaxis_title="Tweet Count",
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    font_color='#ffffff'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Tweet Types
                            tweet_types = patterns.get("tweet_types", {})
                            if tweet_types:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Original Tweets", tweet_types.get("original", 0))
                                with col2:
                                    st.metric("Replies", tweet_types.get("replies", 0))
                                with col3:
                                    st.metric("Quotes", tweet_types.get("quotes", 0))
                        
                        # Engagement Metrics
                        engagement = result.get("engagement", {})
                        if engagement.get("totals"):
                            st.markdown("### Engagement Metrics")
                            
                            totals = engagement["totals"]
                            averages = engagement.get("averages", {})
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Likes", f"{totals.get('likes', 0):,}")
                                st.caption(f"Avg: {averages.get('likes_per_tweet', 0):.1f}/tweet")
                            with col2:
                                st.metric("Total Retweets", f"{totals.get('retweets', 0):,}")
                                st.caption(f"Avg: {averages.get('retweets_per_tweet', 0):.1f}/tweet")
                            with col3:
                                st.metric("Total Replies", f"{totals.get('replies', 0):,}")
                                st.caption(f"Avg: {averages.get('replies_per_tweet', 0):.1f}/tweet")
                            
                            # Top performing tweets
                            top_performing = engagement.get("top_performing", {})
                            if top_performing.get("most_liked"):
                                with st.expander("🔥 Most Liked Tweet"):
                                    st.write(top_performing["most_liked"].get("text", ""))
                                    st.caption(f"❤️ {top_performing['most_liked'].get('likes', 0):,} likes")
                        
                        # Content Analysis
                        content = tweets.get("content_analysis", {})
                        if content.get("top_hashtags"):
                            st.markdown("### Content Analysis")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Top Hashtags**")
                                hashtags = content["top_hashtags"]
                                for tag, count in list(hashtags.items())[:10]:
                                    st.markdown(f"- #{tag} ({count})")
                            
                            with col2:
                                st.markdown("**Top Mentions**")
                                mentions = content.get("top_mentions", {})
                                for user, count in list(mentions.items())[:10]:
                                    st.markdown(f"- @{user} ({count})")
                        
                        # Recent Tweets
                        recent = tweets.get("recent_tweets", [])
                        if recent:
                            st.markdown("### Recent Tweets")
                            
                            for i, tweet in enumerate(recent[:10]):
                                with st.expander(f"Tweet {i+1} - {tweet.get('created_at', '')[:10]}"):
                                    st.write(tweet.get("text", ""))
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.caption(f"❤️ {tweet.get('likes', 0)}")
                                    with col2:
                                        st.caption(f"🔄 {tweet.get('retweets', 0)}")
                                    with col3:
                                        st.caption(f"💬 {tweet.get('replies', 0)}")
                        
                        # Exposures
                        exposures = result.get("exposures", [])
                        if exposures:
                            st.markdown("### Security Exposures")
                            
                            for exp in exposures:
                                severity = exp.get('severity', 'UNKNOWN')
                                color = {
                                    'CRITICAL': '#ef4444',
                                    'HIGH': '#f97316',
                                    'MEDIUM': '#eab308',
                                    'LOW': '#22c55e'
                                }.get(severity, '#6b7280')
                                
                                with st.expander(f"{exp.get('type', 'Exposure')} - {severity}"):
                                    st.markdown(f"**Severity:** <span style='color:{color}'>{severity}</span>", unsafe_allow_html=True)
                                    st.write(exp.get('description', 'N/A'))
                                    if exp.get('value'):
                                        st.markdown(f"**Value:** `{exp['value']}`")
                                    if exp.get('recommendation'):
                                        st.info(exp['recommendation'])
                        
                        # Raw data
                        with st.expander("📄 View raw data"):
                            st.json(result)
                        
                    elif response.status_code == 503:
                        st.error("Twitter analyzer not configured. Please add TWITTER_BEARER_TOKEN to .env file")
                    else:
                        st.error(f"Analysis failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    st.caption("Twitter OSINT powered by Twitter API v2")


# ============================================================================
# IP OSINT PAGE
# ============================================================================
elif page == "IP OSINT":
    st.title("IP Address OSINT Analysis")
    st.caption("Analyze IP addresses for geolocation, network intel, and threats")
    
    ip_address = st.text_input("IP Address", placeholder="Enter IPv4 or IPv6 address...")
    
    if st.button("Analyze", type="primary", use_container_width=True):
        if not ip_address:
            st.error("Please enter an IP address")
        else:
            with st.spinner(f"Analyzing IP: {ip_address}..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/ip/analyze",
                        data={"ip": ip_address}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("error"):
                            st.error(f"Error: {result['error']}")
                        else:
                            # Geolocation Overview
                            st.markdown("### Geolocation")
                            geo = result.get("geolocation", {})
                            location = geo.get("location", {})
                            coords = geo.get("coordinates", {})
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Country", location.get("country", "N/A"))
                            with col2:
                                st.metric("City", location.get("city", "N/A"))
                            with col3:
                                st.metric("Latitude", f"{coords.get('latitude', 0):.4f}" if coords.get('latitude') else "N/A")
                            with col4:
                                st.metric("Longitude", f"{coords.get('longitude', 0):.4f}" if coords.get('longitude') else "N/A")
                            
                            # Map visualization
                            if coords.get("latitude") and coords.get("longitude"):
                                st.markdown("### Location Map")
                                
                                # Use Streamlit's built-in map (no API key needed)
                                map_data = pd.DataFrame({
                                    'lat': [coords['latitude']],
                                    'lon': [coords['longitude']]
                                })
                                
                                st.map(map_data, zoom=10)
                            
                            # Network Intelligence
                            st.markdown("### Network Intelligence")
                            network = geo.get("network", {})
                            
                            with st.expander("🌐 Network Details", expanded=True):
                                if network.get("isp"):
                                    st.markdown(f"**ISP:** {network['isp']}")
                                if network.get("organization"):
                                    st.markdown(f"**Organization:** {network['organization']}")
                                if network.get("as"):
                                    st.markdown(f"**ASN:** {network['as']}")
                                if network.get("as_name"):
                                    st.markdown(f"**AS Name:** {network['as_name']}")
                            
                            # Security Analysis
                            flags = geo.get("flags", {})
                            if any(flags.values()):
                                st.markdown("### Security Flags")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    proxy_icon = "🔴" if flags.get("proxy") else "🟢"  
                                    st.metric("VPN/Proxy", f"{proxy_icon} {'Yes' if flags.get('proxy') else 'No'}")
                                with col2:
                                    hosting_icon = "🟠" if flags.get("hosting") else "🟢"
                                    st.metric("Hosting/DC", f"{hosting_icon} {'Yes' if flags.get('hosting') else 'No'}")
                                with col3:
                                    mobile_icon = "🔵" if flags.get("mobile") else "🟢"
                                    st.metric("Mobile", f"{mobile_icon} {'Yes' if flags.get('mobile') else 'No'}")
                            
                            # DNS Information
                            dns = result.get("dns", {})
                            if dns.get("hostname"):
                                st.markdown("### DNS Information")
                                st.success(f"**Hostname:** {dns['hostname']}")
                            
                            # Threat Intelligence
                            threat = result.get("threat_intelligence", {})
                            if threat and not threat.get("message"):
                                if threat.get("abuse_confidence_score") is not None:
                                    st.markdown("### Threat Intelligence")
                                    
                                    score = threat["abuse_confidence_score"]
                                    score_color = "#ef4444" if score > 75 else "#f97316" if score > 50 else "#eab308" if score > 25 else "#22c55e"
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Abuse Score", f"{score}%")
                                    with col2:
                                        st.metric("Total Reports", threat.get("total_reports", 0))
                                    with col3:
                                        st.metric("Reporters", threat.get("num_distinct_users", 0))
                                    
                                    st.progress(score / 100, text=f"Confidence: {score}%")
                            
                            # Intelligence Summary
                            summary = result.get("intelligence_summary", {})
                            if summary:
                                st.markdown("### Intelligence Summary")
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown(f"**IP Type:** {summary.get('ip_type', 'N/A')}")
                                    st.markdown(f"**ISP:** {summary.get('isp', 'N/A')}")
                                    st.markdown(f"**Threat Level:** {summary.get('threat_level', 'N/A')}")
                                
                                with col2:
                                    st.markdown(f"**Location:** {summary.get('geographic_location', 'N/A')}")
                                    st.markdown(f"**Organization:** {summary.get('organization', 'N/A')}")
                                    st.markdown(f"**Exposure Risk:** {summary.get('exposure_risk', 'N/A')}")
                                
                                if summary.get('key_findings'):
                                    st.markdown("**Key Findings:**")
                                    for finding in summary['key_findings']:
                                        st.markdown(f"- {finding}")
                            
                            # Exposures
                            exposures = result.get("exposures", [])
                            if exposures:
                                st.markdown("### Security Exposures")
                                
                                for exp in exposures:
                                    severity = exp.get('severity', 'UNKNOWN')
                                    color = {
                                        'CRITICAL': '#ef4444',
                                        'HIGH': '#f97316',
                                        'MEDIUM': '#eab308',
                                        'LOW': '#22c55e'
                                    }.get(severity, '#6b7280')
                                    
                                    with st.expander(f"{exp.get('type', 'Exposure')} - {severity}"):
                                        st.markdown(f"**Severity:** <span style='color:{color}'>{severity}</span>", unsafe_allow_html=True)
                                        st.write(exp.get('description', 'N/A'))
                                        if exp.get('value'):
                                            st.markdown(f"**Value:** `{exp['value']}`")
                                        if exp.get('recommendation'):
                                            st.info(exp['recommendation'])
                            
                            # Raw data
                            with st.expander("📄 View raw data"):
                                st.json(result)
                    
                    else:
                        st.error(f"Analysis failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    st.caption("IP OSINT powered by free geolocation APIs")


# ============================================================================
# SPIDERFOOT OSINT PAGE
# ============================================================================
elif page == "SpiderFoot OSINT":
    st.title("🕷️ SpiderFoot OSINT")
    
    # Check if SpiderFoot is available
    try:
        health_response = requests.get(f"{API_URL}/api/spiderfoot/health", timeout=2)
        spiderfoot_available = health_response.json().get("available", False)
    except:
        spiderfoot_available = False
    
    if not spiderfoot_available:
        st.error("⚠️ SpiderFoot is not running")
        st.info("Start SpiderFoot to access 200+ OSINT modules")
        st.code("cd C:\\Users\\karbi\\spiderfoot && docker-compose up -d", language="bash")
        st.markdown("---")
        st.markdown("Once started, refresh this page to access SpiderFoot UI")
    else:
        st.success("✅ SpiderFoot Active")
        
        # Info banner
        st.info("🕷️ **SpiderFoot v4.0** - Comprehensive OSINT automation with 200+ intelligence modules embedded below")
        
        # Embed SpiderFoot UI in iframe
        st.components.v1.iframe(
            src="http://localhost:5001",
            height=800,
            scrolling=True
        )
        
        st.markdown("---")
        st.caption("SpiderFoot running at http://localhost:5001 • Open in new tab for full-screen experience")


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