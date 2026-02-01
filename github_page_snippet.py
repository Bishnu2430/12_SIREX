
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


