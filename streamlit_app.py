import streamlit as st
import requests, json, pandas as pd, plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="OSINT Exposure Intelligence", page_icon="🔍", layout="wide")

API_BASE_URL = "http://localhost:8000"

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = None

st.sidebar.markdown("# 🔍 OSINT Intelligence")
page = st.sidebar.radio("Navigation", ["📁 Media Analysis", "👁️ Agent Observability", "🕸️ Intelligence Graph"])

# PAGE 1: MEDIA ANALYSIS
if page == "📁 Media Analysis":
    st.title("📁 Media Upload & Analysis")
    uploaded_file = st.file_uploader("Choose a media file", type=['jpg', 'jpeg', 'png', 'mp4', 'mov', 'avi', 'wav', 'mp3'])
    
    if uploaded_file:
        st.success(f"File: {uploaded_file.name} ({uploaded_file.size/1024:.2f} KB)")
        if uploaded_file.type.startswith('image'):
            st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        
        if st.button("🚀 Analyze Media"):
            with st.spinner("Analyzing..."):
                try:
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_BASE_URL}/analyze", files=files, timeout=300)
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.analysis_result = result
                        st.session_state.session_id = result.get('session_id')
                        st.success("✅ Complete!")
                        st.rerun()
                    else:
                        st.error(f"Failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        report = result.get('report', {})
        summary = report.get('summary', {})
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Persons", summary.get('persons_detected', 0))
        col2.metric("Locations", summary.get('locations_detected', 0))
        col3.metric("Organizations", summary.get('organizations_detected', 0))
        col4.metric("Events", summary.get('events_detected', 0))
        
        st.markdown("### 🤖 OSINT Analyst Report")
        with st.container(border=True):
            st.markdown(report.get('llm_analysis', 'No detailed analysis available.'))
            
        with st.expander("📂 Raw Intelligence Data (EXIF, OCR, Audio)"):
            raw = report.get('raw_intelligence', {})
            tab1, tab2, tab3 = st.tabs(["metadata", "ocr", "audio"])
            with tab1: st.json(raw.get('metadata', {}))
            with tab2: st.json(raw.get('ocr', []))
            with tab3: st.json(raw.get('audio', {}))

        st.markdown("### ⚠️ Exposure Analysis")
        for idx, exp in enumerate(report.get('exposure_analysis', [])):
            severity = exp.get('severity', 'UNKNOWN')
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
            
            with st.expander(f"{icon} Exposure #{idx+1}: {exp.get('exposure_type')} - {severity}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Entity:** {exp.get('entity')}")
                    st.write(f"**Risk Score:** {exp.get('risk_score')}")
                with col2:
                    misuse = exp.get('simulated_misuse', {})
                    st.write(f"**Misuse:** {misuse.get('misuse', 'N/A')}")
                    st.write(f"**Impact:** {misuse.get('impact', 'N/A')}")
                
                for rec in exp.get('recommendations', []):
                    st.markdown(f"- {rec}")

# PAGE 2: OBSERVABILITY
elif page == "👁️ Agent Observability":
    st.title("👁️ Agent Observability")
    
    if st.session_state.session_id:
        st.info(f"Session: `{st.session_state.session_id}`")
        if st.button("🔄 Refresh"):
            st.rerun()
        
        try:
            response = requests.get(f"{API_BASE_URL}/logs/{st.session_state.session_id}")
            if response.status_code == 200:
                logs = response.json().get('logs', [])
                if logs:
                    st.write(f"### 📊 Pipeline Events ({len(logs)})")
                    for log in logs:
                        with st.expander(f"{log['stage']} - {log['timestamp']}"):
                            st.json(log['data'])
                else:
                    st.warning("No logs yet")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("No active session")

# PAGE 3: GRAPH
elif page == "🕸️ Intelligence Graph":
    st.title("🕸️ Intelligence Graph")
    
    if st.button("🔄 Reload"):
        st.rerun()
    
    try:
        response = requests.get(f"{API_BASE_URL}/graph")
        if response.status_code == 200:
            graph_data = response.json()
            nodes = graph_data.get('nodes', [])
            links = graph_data.get('links', [])
            
            if nodes and links:
                st.success(f"📊 {len(nodes)} nodes, {len(links)} edges")
                
                # Simple graph viz
                import math
                node_ids = {node['id']: idx for idx, node in enumerate(nodes)}
                
                edge_x, edge_y = [], []
                for link in links:
                    src_idx = node_ids.get(link['source'])
                    tgt_idx = node_ids.get(link['target'])
                    if src_idx is not None and tgt_idx is not None:
                        ang_s = 2 * math.pi * src_idx / len(nodes)
                        ang_t = 2 * math.pi * tgt_idx / len(nodes)
                        edge_x.extend([math.cos(ang_s), math.cos(ang_t), None])
                        edge_y.extend([math.sin(ang_s), math.sin(ang_t), None])
                
                node_x, node_y, node_text = [], [], []
                for idx, node in enumerate(nodes):
                    ang = 2 * math.pi * idx / len(nodes)
                    node_x.append(math.cos(ang))
                    node_y.append(math.sin(ang))
                    node_text.append(f"{node.get('type')}: {node['id']}")
                
                fig = go.Figure(data=[
                    go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=0.5, color='#888'), hoverinfo='none'),
                    go.Scatter(x=node_x, y=node_y, mode='markers', hovertext=node_text, marker=dict(size=15, color='lightblue'))
                ])
                fig.update_layout(showlegend=False, hovermode='closest', height=600,
                                  xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                  yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 Node Details"):
                    st.dataframe(pd.DataFrame(nodes))
            else:
                st.info("No graph data. Analyze media first.")
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")
st.markdown("<div style='text-align:center'>🔍 OSINT Exposure Intelligence System v1.0</div>", unsafe_allow_html=True)