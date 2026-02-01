
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


