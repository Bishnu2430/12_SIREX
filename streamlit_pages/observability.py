import streamlit as st
import requests
import json
from datetime import datetime

def show():
    st.title("👁️ Agent Observability")
    st.markdown("Monitor the agent's reasoning process and decision-making pipeline")
    
    # Get available sessions
    try:
        response = requests.get('http://localhost:8000/sessions', timeout=5)
        if response.status_code == 200:
            sessions_data = response.json()
            sessions = sessions_data.get('sessions', [])
        else:
            sessions = []
    except:
        st.warning("⚠️ Cannot connect to API server. Please ensure FastAPI is running.")
        sessions = []
    
    if not sessions:
        st.info("📭 No analysis sessions found. Upload and analyze media first!")
        return
    
    # Session selector
    st.markdown("### 📋 Select Session")
    selected_session = st.selectbox(
        "Choose a session to view logs",
        sessions,
        format_func=lambda x: f"Session {x}",
        help="Select a session ID to view its processing logs"
    )
    
    if selected_session:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"#### Session: `{selected_session}`")
        
        with col2:
            refresh_button = st.button("🔄 Refresh", use_container_width=True)
        
        try:
            response = requests.get(f'http://localhost:8000/session/{selected_session}/logs', timeout=5)
            
            if response.status_code == 200:
                logs_data = response.json()
                logs = logs_data.get('logs', [])
                
                if not logs:
                    st.warning("No logs found for this session")
                    return
                
                st.markdown(f"### 📊 Processing Pipeline ({len(logs)} events)")
                
                # Create tabs for different views
                tab1, tab2, tab3, tab4 = st.tabs(["🔄 Timeline", "📈 Stage Summary", "🧠 Intelligence Events", "📝 Raw Logs"])
                
                with tab1:
                    st.markdown("#### Event Timeline")
                    
                    for idx, log in enumerate(logs):
                        timestamp = log.get('timestamp', 'Unknown')
                        stage = log.get('stage', 'Unknown')
                        data = log.get('data', {})
                        
                        # Color code by stage
                        stage_colors = {
                            'pipeline_start': '🟢',
                            'entities_built': '🔵',
                            'relationships_built': '🟣',
                            'exposures_mapped': '🟠',
                            'misuse_simulated': '🔴',
                            'hypotheses_generated': '🧠',
                            'behavior_patterns_detected': '📈',
                            'spatial_temporal_insights': '🌍',
                            'risk_assessed': '⚠️',
                            'learning_update': '📚',
                            'pipeline_complete': '✅'
                        }
                        
                        icon = stage_colors.get(stage, '⚪')
                        
                        with st.expander(f"{icon} {idx+1}. {stage.replace('_', ' ').title()} - {timestamp}"):
                            if isinstance(data, dict):
                                # Format specific stages
                                if stage == 'entities_built':
                                    st.markdown("**Entities Detected:**")
                                    for entity_type, entities in data.items():
                                        if entities:
                                            st.markdown(f"- **{entity_type.title()}**: {len(entities)} found")
                                
                                elif stage == 'exposures_mapped':
                                    st.markdown(f"**Total Exposures**: {len(data)}")
                                    exposure_types = {}
                                    for exp in data:
                                        exp_type = exp.get('type', 'Unknown')
                                        exposure_types[exp_type] = exposure_types.get(exp_type, 0) + 1
                                    
                                    for exp_type, count in exposure_types.items():
                                        st.markdown(f"- {exp_type}: {count}")
                                
                                elif stage == 'risk_assessed':
                                    st.markdown("**Risk Assessment:**")
                                    severity_counts = {}
                                    for risk in data:
                                        severity = risk.get('severity', 'Unknown')
                                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                                    
                                    col_a, col_b, col_c, col_d = st.columns(4)
                                    with col_a:
                                        st.metric("CRITICAL", severity_counts.get('CRITICAL', 0))
                                    with col_b:
                                        st.metric("HIGH", severity_counts.get('HIGH', 0))
                                    with col_c:
                                        st.metric("MEDIUM", severity_counts.get('MEDIUM', 0))
                                    with col_d:
                                        st.metric("LOW", severity_counts.get('LOW', 0))
                                
                                elif stage == 'hypotheses_generated' and data:
                                    st.markdown("**Generated Hypotheses:**")
                                    for hyp in data:
                                        st.markdown(f"- {hyp.get('hypothesis')} (Confidence: {hyp.get('confidence')})")
                                
                                else:
                                    st.json(data)
                            else:
                                st.write(data)
                
                with tab2:
                    st.markdown("#### Pipeline Stage Summary")
                    
                    # Count events by stage
                    stage_counts = {}
                    for log in logs:
                        stage = log.get('stage', 'Unknown')
                        stage_counts[stage] = stage_counts.get(stage, 0) + 1
                    
                    # Display as metrics
                    cols = st.columns(3)
                    for idx, (stage, count) in enumerate(stage_counts.items()):
                        with cols[idx % 3]:
                            st.metric(
                                stage.replace('_', ' ').title(),
                                count,
                                help=f"Number of {stage} events"
                            )
                
                with tab3:
                    st.markdown("#### Intelligence Layer Events")
                    
                    intelligence_stages = [
                        'hypotheses_generated',
                        'behavior_patterns_detected',
                        'spatial_temporal_insights',
                        'learning_update'
                    ]
                    
                    intelligence_logs = [log for log in logs if log.get('stage') in intelligence_stages]
                    
                    if intelligence_logs:
                        for log in intelligence_logs:
                            stage = log.get('stage', '')
                            data = log.get('data', {})
                            
                            st.markdown(f"**{stage.replace('_', ' ').title()}**")
                            
                            if isinstance(data, list):
                                for item in data:
                                    st.json(item)
                            else:
                                st.json(data)
                            
                            st.markdown("---")
                    else:
                        st.info("No intelligence layer events in this session")
                
                with tab4:
                    st.markdown("#### Raw Log Data")
                    st.json(logs)
                
                # Download logs
                st.markdown("### 💾 Export Logs")
                logs_json = json.dumps(logs, indent=2)
                st.download_button(
                    label="📥 Download Logs (JSON)",
                    data=logs_json,
                    file_name=f"logs_{selected_session}.json",
                    mime="application/json"
                )
                
            else:
                st.error(f"Failed to fetch logs: {response.text}")
                
        except Exception as e:
            st.error(f"Error fetching logs: {str(e)}")
    
    # Information panel
    with st.expander("ℹ️ About Agent Observability"):
        st.markdown("""
        ### What is Agent Observability?
        
        This page shows the internal reasoning and decision-making process of the AI agent as it analyzes media.
        
        ### Pipeline Stages
        
        1. **Pipeline Start**: Initialization
        2. **Entities Built**: Person, location, organization detection
        3. **Relationships Built**: Entity relationship mapping
        4. **Exposures Mapped**: Privacy exposure classification
        5. **Misuse Simulated**: Adversarial scenario modeling
        6. **Hypotheses Generated**: Intelligence reasoning
        7. **Behavior Patterns Detected**: Pattern analysis
        8. **Spatial-Temporal Insights**: Location & time reasoning
        9. **Risk Assessed**: Final risk scoring
        10. **Learning Update**: Memory and improvement
        11. **Pipeline Complete**: Finalization
        
        ### Why This Matters
        
        - **Transparency**: See exactly how decisions are made
        - **Debugging**: Understand where issues occur
        - **Trust**: Verify the agent's reasoning
        - **Learning**: Understand the intelligence process
        """)