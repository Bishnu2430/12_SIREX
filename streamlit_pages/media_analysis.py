import streamlit as st
import requests
import json
import os
from datetime import datetime

def show():
    st.title("🎯 Media Analysis")
    st.markdown("Upload images, videos, or audio files for OSINT exposure intelligence analysis")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a media file",
        type=['jpg', 'jpeg', 'png', 'mp4', 'mov', 'avi', 'wav', 'mp3'],
        help="Supported formats: Images (JPG, PNG), Videos (MP4, MOV, AVI), Audio (WAV, MP3)"
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        analyze_button = st.button("🔍 Analyze Media", type="primary", use_container_width=True)
    
    if uploaded_file is not None:
        # Display preview
        st.markdown("### 📁 File Preview")
        
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.2f} KB",
            "File type": uploaded_file.type
        }
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.json(file_details)
        
        with col_b:
            if uploaded_file.type.startswith('image'):
                st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
            elif uploaded_file.type.startswith('video'):
                st.video(uploaded_file)
            elif uploaded_file.type.startswith('audio'):
                st.audio(uploaded_file)
        
        if analyze_button:
            with st.spinner('🔄 Analyzing media... This may take a few minutes...'):
                try:
                    # Save file temporarily
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Call API (assuming it's running locally)
                    files = {'file': open(temp_path, 'rb')}
                    
                    # Try local API first
                    try:
                        response = requests.post('http://localhost:8000/analyze', files=files, timeout=300)
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to API server. Please ensure FastAPI is running on port 8000")
                        st.code("uvicorn app.main:app --reload --port 8000", language="bash")
                        return
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("✅ Analysis Complete!")
                        
                        # Display summary
                        st.markdown("### 📊 Analysis Summary")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        summary = result.get('summary', {})
                        
                        with col1:
                            st.metric(
                                "Entities Found",
                                summary.get('entities_found', 0),
                                help="Persons, locations, organizations detected"
                            )
                        
                        with col2:
                            st.metric(
                                "Exposures Identified",
                                summary.get('exposures_identified', 0),
                                help="Privacy and security exposures found"
                            )
                        
                        with col3:
                            risk_level = summary.get('risk_level', 'UNKNOWN')
                            risk_color = {
                                'CRITICAL': '🔴',
                                'HIGH': '🟠',
                                'MEDIUM': '🟡',
                                'LOW': '🟢'
                            }.get(risk_level, '⚪')
                            
                            st.metric(
                                "Risk Level",
                                f"{risk_color} {risk_level}"
                            )
                        
                        # Display full report
                        st.markdown("### 📄 Detailed Report")
                        
                        report = result.get('report', {})
                        
                        # Entity Summary
                        with st.expander("👥 Detected Entities", expanded=True):
                            entity_summary = report.get('summary', {})
                            st.json(entity_summary)
                        
                        # Exposure Analysis
                        with st.expander("⚠️ Exposure Analysis", expanded=True):
                            exposures = report.get('exposure_analysis', [])
                            
                            for idx, exposure in enumerate(exposures):
                                severity = exposure.get('severity', 'UNKNOWN')
                                
                                if severity == 'CRITICAL':
                                    box_class = 'danger-box'
                                elif severity == 'HIGH':
                                    box_class = 'warning-box'
                                else:
                                    box_class = 'success-box'
                                
                                st.markdown(f'<div class="{box_class}">', unsafe_allow_html=True)
                                st.markdown(f"**Exposure {idx+1}: {exposure.get('exposure_type')}**")
                                st.markdown(f"**Entity:** {exposure.get('entity')}")
                                st.markdown(f"**Risk Score:** {exposure.get('risk_score')}")
                                st.markdown(f"**Severity:** {severity}")
                                
                                misuse = exposure.get('simulated_misuse', {})
                                if misuse:
                                    st.markdown(f"**Potential Misuse:** {misuse.get('misuse')}")
                                    st.markdown(f"**Impact:** {misuse.get('impact')}")
                                    st.markdown(f"**Likelihood:** {misuse.get('likelihood')}")
                                
                                recommendations = exposure.get('recommendations', [])
                                if recommendations:
                                    st.markdown("**🛡️ Recommendations:**")
                                    for rec in recommendations:
                                        st.markdown(f"- {rec}")
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Reasoning Layer
                        reasoning = report.get('reasoning', {})
                        
                        if reasoning.get('hypotheses'):
                            with st.expander("🧠 Intelligence Hypotheses"):
                                for hyp in reasoning['hypotheses']:
                                    st.markdown(f"- **{hyp.get('hypothesis')}** (Confidence: {hyp.get('confidence')})")
                        
                        if reasoning.get('behavior_patterns'):
                            with st.expander("📈 Behavior Patterns"):
                                for pattern in reasoning['behavior_patterns']:
                                    st.markdown(f"- **{pattern.get('pattern')}**: {pattern.get('risk_implication')} (Severity: {pattern.get('severity')})")
                        
                        if reasoning.get('spatial_temporal_insights'):
                            with st.expander("🌍 Spatial-Temporal Insights"):
                                for insight in reasoning['spatial_temporal_insights']:
                                    st.markdown(f"- **{insight.get('insight')}**: {insight.get('risk')}")
                        
                        # Download report
                        st.markdown("### 💾 Export")
                        
                        report_json = json.dumps(result, indent=2)
                        st.download_button(
                            label="📥 Download Full Report (JSON)",
                            data=report_json,
                            file_name=f"osint_report_{result.get('session_id', 'unknown')}.json",
                            mime="application/json"
                        )
                        
                        # Session ID for tracking
                        st.info(f"📌 Session ID: `{result.get('session_id')}` - Use this to view logs and graph")
                        
                    else:
                        st.error(f"❌ Analysis failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    st.exception(e)
    
    # Instructions
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        ### Analysis Process
        
        1. **Upload Media**: Choose an image, video, or audio file
        2. **Click Analyze**: The system will process the media through multiple AI models
        3. **Review Results**: Examine detected entities, exposures, and risk assessment
        4. **Take Action**: Follow recommendations to reduce exposure risks
        
        ### What Gets Analyzed
        
        - **Visual**: Faces, objects, scenes, landmarks, text
        - **Audio**: Speech, language, sounds, speaker identity
        - **Metadata**: GPS coordinates, timestamps, device information
        - **Context**: Entity relationships, patterns, behavioral analysis
        
        ### Privacy & Security
        
        - All analysis is performed locally
        - No data is sent to external servers
        - Files are processed in isolated sessions
        - You can delete session data at any time
        """)