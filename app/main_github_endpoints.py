

# ==================== GitHub OSINT Endpoints ====================

@app.post("/api/github/analyze")
async def analyze_github_user(username: str = Form(...)):
    """
    Analyze a GitHub user
    
    Parameters:
        username: GitHub username to analyze
    
    Returns:
        Comprehensive GitHub OSINT analysis
    """
    try:
        if not github_analyzer:
            raise HTTPException(status_code=503, detail="GitHub analyzer not configured. Add GITHUB_ACCESS_TOKEN to .env")
        
        logger.info(f"GitHub analysis request for: {username}")
        
        # Perform analysis
        results = github_analyzer.analyze_user(username)
        
        # Add to knowledge graph
        try:
            _add_github_to_graph(username, results)
        except Exception as e:
            logger.warning(f"Failed to add GitHub data to graph: {e}")
        
        # Sanitize and return
        clean_results = sanitize_for_json(results)
        return JSONResponse(content=clean_results)
        
    except Exception as e:
        logger.error(f"GitHub analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/github/user/{username}")
async def get_github_profile(username: str):
    """Get basic GitHub profile info"""
    try:
        if not github_analyzer:
            raise HTTPException(status_code=503, detail="GitHub analyzer not configured")
        
        # Just get profile
        response = github_analyzer.session.get(f"{github_analyzer.base_url}/users/{username}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        
        return JSONResponse(content=response.json())
        
    except Exception as e:
        logger.error(f"GitHub profile fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _add_github_to_graph(username: str, results: Dict[str, Any]):
    """Add GitHub analysis results to knowledge graph"""
    try:
        profile = results.get("profile", {})
        repos = results.get("repositories", {})
        network = results.get("network", {})
        
        # Add user entity
        user_id = f"github_user_{username}"
        analyzer.graph.add_entity(
            entity_id=user_id,
            entity_type="GitHubUser",
            properties={
                "username": username,
                "name": profile.get("basic_info", {}).get("name"),
                "bio": profile.get("basic_info", {}).get("bio"),
                "location": profile.get("basic_info", {}).get("location"),
                "company": profile.get("basic_info", {}).get("company"),
                "email": profile.get("basic_info", {}).get("email"),
                "followers": profile.get("account_metrics", {}).get("followers"),
                "following": profile.get("account_metrics", {}).get("following"),
                "public_repos": profile.get("account_metrics", {}).get("public_repos"),
                "profile_url": profile.get("urls", {}).get("profile_url")
            },
            source_file="github_osint"
        )
        
        # Add organizations
        for org in network.get("organizations", []):
            org_id = f"github_org_{org['name']}"
            analyzer.graph.add_entity(
                entity_id=org_id,
                entity_type="Organization",
                properties={
                    "name": org['name'],
                    "url": org.get('url'),
                    "platform": "GitHub"
                },
                source_file="github_osint"
            )
            
            # Add membership relationship
            analyzer.graph.add_relationship(
                source_id=user_id,
                target_id=org_id,
                relationship_type="member_of",
                properties={"platform": "GitHub"}
            )
        
        logger.info(f"Added GitHub data to knowledge graph: {username}")
        
    except Exception as e:
        logger.error(f"Failed to add GitHub data to graph: {e}")
        raise
