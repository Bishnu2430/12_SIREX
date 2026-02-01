"""
FastAPI Server for OSINT Backend
Provides RESTful API for media analysis and knowledge graph access
"""

import os
import sys
from pathlib import Path
from typing import Optional
import shutil
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from config import settings
from core.osint_analyzer import OSINTAnalyzer
from core.github.github_analyzer import GitHubAnalyzer
from core.twitter.twitter_analyzer import TwitterAnalyzer
from core.ip.ip_analyzer import IPAnalyzer
from core.spiderfoot.spiderfoot_client import SpiderFootClient

# Configure logger
logger.add(
    "logs/osint_backend.log",
    rotation="100 MB",
    retention="30 days",
    level="INFO"
)

# Initialize FastAPI
app = FastAPI(
    title="OSINT Backend API",
    description="Comprehensive media analysis with maximum intelligence extraction",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OSINT Analyzer
analyzer = OSINTAnalyzer(graph_storage_path="knowledge_graph.json")

# Initialize GitHub Analyzer
github_analyzer = None
if settings.GITHUB_ACCESS_TOKEN:
    try:
        github_analyzer = GitHubAnalyzer(settings.GITHUB_ACCESS_TOKEN)
        logger.info("✓ GitHub analyzer initialized")
    except Exception as e:
        logger.warning(f"GitHub analyzer initialization failed: {e}")
else:
    logger.warning("GitHub access token not configured")

# Initialize Twitter Analyzer
twitter_analyzer = None
if settings.TWITTER_BEARER_TOKEN:
    try:
        twitter_analyzer = TwitterAnalyzer(settings.TWITTER_BEARER_TOKEN)
        logger.info("✓ Twitter analyzer initialized")
    except Exception as e:
        logger.warning(f"Twitter analyzer initialization failed: {e}")
else:
    logger.warning("Twitter bearer token not configured")

# Initialize IP Analyzer (no API key required, but AbuseIPDB is optional)
ip_analyzer = IPAnalyzer(abuseipdb_key=settings.ABUSEIPDB_API_KEY if settings.ABUSEIPDB_API_KEY else None)
logger.info("✓ IP analyzer initialized")

# Initialize SpiderFoot Client
spiderfoot_client = SpiderFootClient(base_url="http://localhost:5001")
if spiderfoot_client.check_health():
    logger.info("✓ SpiderFoot client initialized and connected")
else:
    logger.warning("SpiderFoot not accessible at http://localhost:5001")

# Request/Response Models
class AnalysisRequest(BaseModel):
    context: Optional[str] = "OSINT Investigation"
    update_graph: Optional[bool] = True

class GraphQueryRequest(BaseModel):
    entity_type: Optional[str] = None
    properties: Optional[dict] = {}

# Storage for analysis results
analysis_cache = {}


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("=== OSINT Backend Starting ===")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Output directory: {settings.OUTPUT_DIR}")
    
    # Ensure directories exist
    settings.UPLOAD_DIR.mkdir(exist_ok=True)
    settings.OUTPUT_DIR.mkdir(exist_ok=True)
    settings.CACHE_DIR.mkdir(exist_ok=True)
    
    # Log component status
    logger.info("Analyzer components ready")


@app.get("/")
async def root():
    """API root"""
    return {
        "service": "OSINT Backend API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze",
            "graph": "/api/graph/*",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    stats = analyzer.get_graph_statistics()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "llm": "operational" if analyzer.llm.model else "not_configured",
            "vision": "operational" if analyzer.vision.is_enabled() else "not_configured",
            "audio": "operational",
            "metadata": "operational",
            "graph": "operational"
        },
        "graph_stats": stats
    }


import math
import numpy as np

def sanitize_for_json(obj):
    """Recursively replace NaN/Infinity/booleans/numpy types with JSON-safe values"""
    # Handle numpy boolean types
    if isinstance(obj, (np.bool_, np.generic)):
        return int(obj)
    # Handle Python boolean (must check before int since bool is subclass of int)
    elif isinstance(obj, bool):
        return 1 if obj else 0
    # Handle numpy integers and floats
    elif isinstance(obj, (np.integer, np.floating)):
        obj = float(obj)
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    # Handle Python floats
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    # Recursively handle dicts
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    # Recursively handle lists
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    # Handle numpy arrays
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    return obj





@app.post("/api/analyze")
async def analyze_media(
    file: UploadFile = File(...),
    context: str = Form("OSINT Investigation"),
    update_graph: bool = Form(True),
    background_tasks: BackgroundTasks = None
):
    """
    Analyze uploaded media file
    
    Returns comprehensive analysis cleaned of non-JSON compliant values
    """
    try:
        # Validate file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Save uploaded file
        file_path = settings.UPLOAD_DIR / file.filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} ({file_size / 1024:.1f} KB)")
        
        # Run analysis
        try:
            results = analyzer.analyze_media(
                file_path=str(file_path),
                context=context,
                update_graph=update_graph
            )
            
            # Cache results
            analysis_id = f"{int(time.time())}_{file.filename}"
            analysis_cache[analysis_id] = results
            results["analysis_id"] = analysis_id
            
            # Sanitize to prevent JSON errors (NaN/Infinity)
            clean_results = sanitize_for_json(results)
            
            return JSONResponse(content=clean_results)
            
        finally:
            # Clean up upload file in background
            if background_tasks:
                background_tasks.add_task(cleanup_file, file_path)
            elif file_path.exists():
                try:
                    os.remove(file_path)
                except:
                    pass
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get cached analysis results"""
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_cache[analysis_id]


@app.get("/api/graph/statistics")
async def get_graph_statistics():
    """Get knowledge graph statistics"""
    return analyzer.get_graph_statistics()


@app.get("/api/graph/export")
async def export_graph():
    """Export knowledge graph for visualization"""
    return analyzer.export_graph_visualization()


@app.get("/api/graph/entity/{entity_id}")
async def get_entity(entity_id: str):
    """Get entity details"""
    entity = analyzer.graph.get_entity(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity


@app.get("/api/graph/entity/{entity_id}/network")
async def get_entity_network(
    entity_id: str,
    depth: int = Query(default=2, ge=1, le=5)
):
    """Get network of entities connected to this entity"""
    network = analyzer.get_entity_network(entity_id, depth=depth)
    
    if not network:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return network


@app.get("/api/graph/entity/{entity_id}/relationships")
async def get_entity_relationships(
    entity_id: str,
    direction: str = Query(default="both", regex="^(incoming|outgoing|both)$")
):
    """Get all relationships for an entity"""
    relationships = analyzer.graph.get_relationships(entity_id, direction=direction)
    
    return {
        "entity_id": entity_id,
        "direction": direction,
        "relationships": relationships,
        "count": len(relationships)
    }


@app.post("/api/graph/search")
async def search_entities(request: GraphQueryRequest):
    """Search for entities matching criteria"""
    results = analyzer.graph.find_entity(
        entity_type=request.entity_type,
        **request.properties
    )
    
    return {
        "query": {
            "entity_type": request.entity_type,
            "properties": request.properties
        },
        "results": results,
        "count": len(results)
    }


@app.delete("/api/graph/clear")
async def clear_graph():
    """Clear all knowledge graph data (use with caution)"""
    analyzer.graph.clear()
    return {"status": "success", "message": "Knowledge graph cleared"}


@app.get("/api/graph/location/nearby")
async def find_nearby_locations(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(default=1.0, ge=0.1, le=100.0)
):
    """Find locations within radius of coordinates"""
    matches = analyzer.graph.match_location(latitude, longitude, radius_km)
    
    entities = [analyzer.graph.get_entity(entity_id) for entity_id in matches]
    
    return {
        "query": {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km
        },
        "matches": entities,
        "count": len(entities)
    }


@app.get("/api/model/info")
async def get_model_info():
    """Get information about active AI models"""
    return {
        "llm": analyzer.llm.get_model_info(),
        "vision": {
            "enabled": analyzer.vision.is_enabled(),
            "service": "Google Cloud Vision API"
        },
        "audio": {
            "enabled": True,
            "features": ["transcription", "acoustic_analysis", "speech_characteristics"]
        }
    }


@app.post("/api/test/connection")
async def test_connections():
    """Test all component connections"""
    results = {
        "llm": analyzer.llm.test_connection(),
        "vision": analyzer.vision.is_enabled(),
        "audio": True,  # Audio analyzer doesn't need external connection
        "graph": True
    }
    
    return {
        "status": "success" if all(results.values()) else "partial",
        "components": results
    }


# Utility functions
def cleanup_file(file_path: Path):
    """Clean up temporary file"""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")


# ==================== GitHub OSINT Endpoints ====================

@app.post("/api/github/analyze")
async def analyze_github_user(username: str = Form(...)):
    """Analyze a GitHub user"""
    try:
        if not github_analyzer:
            raise HTTPException(status_code=503, detail="GitHub analyzer not configured. Add GITHUB_ACCESS_TOKEN to .env")
        
        logger.info(f"GitHub analysis request for: {username}")
        
        results = github_analyzer.analyze_user(username)
        
        # Add to knowledge graph
        try:
            profile = results.get("profile", {})
            user_id = f"github_user_{username}"
            analyzer.graph.add_entity(
                entity_id=user_id,
                entity_type="GitHubUser",
                properties={
                    "username": username,
                    "name": profile.get("basic_info", {}).get("name"),
                    "followers": profile.get("account_metrics", {}).get("followers"),
                    "public_repos": profile.get("account_metrics", {}).get("public_repos"),
                },
                source_file="github_osint"
            )
        except Exception as e:
            logger.warning(f"Failed to add GitHub data to graph: {e}")
        
        clean_results = sanitize_for_json(results)
        return JSONResponse(content=clean_results)
        
    except Exception as e:
        logger.error(f"GitHub analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Twitter OSINT Endpoints ====================

@app.post("/api/twitter/analyze")
async def analyze_twitter_user(username: str = Form(...)):
    """Analyze a Twitter/X user"""
    try:
        if not twitter_analyzer:
            raise HTTPException(status_code=503, detail="Twitter analyzer not configured. Add TWITTER_BEARER_TOKEN to .env")
        
        logger.info(f"Twitter analysis request for: @{username}")
        
        results = twitter_analyzer.analyze_user(username)
        
        # Add to knowledge graph
        try:
            profile = results.get("profile", {})
            user_id = f"twitter_user_{username}"
            analyzer.graph.add_entity(
                entity_id=user_id,
                entity_type="TwitterUser",
                properties={
                    "username": username,
                    "name": profile.get("basic_info", {}).get("name"),
                    "followers": profile.get("account_metrics", {}).get("followers"),
                    "tweets": profile.get("account_metrics", {}).get("tweets"),
                },
                source_file="twitter_osint"
            )
        except Exception as e:
            logger.warning(f"Failed to add Twitter data to graph: {e}")
        
        clean_results = sanitize_for_json(results)
        return JSONResponse(content=clean_results)
        
    except Exception as e:
        logger.error(f"Twitter analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IP OSINT Endpoints ====================

@app.post("/api/ip/analyze")
async def analyze_ip_address(ip: str = Form(...)):
    """Analyze an IP address"""
    try:
        logger.info(f"IP analysis request for: {ip}")
        
        results = ip_analyzer.analyze_ip(ip)
        
        # Add to knowledge graph
        try:
            geo = results.get("geolocation", {})
            location = geo.get("location", {})
            network = geo.get("network", {})
            
            ip_id = f"ip_{ip.replace('.', '_').replace(':', '_')}"
            analyzer.graph.add_entity(
                entity_id=ip_id,
                entity_type="IPAddress",
                properties={
                    "ip": ip,
                    "country": location.get("country"),
                    "city": location.get("city"),
                    "isp": network.get("isp"),
                    "organization": network.get("organization"),
                },
                source_file="ip_osint"
            )
        except Exception as e:
            logger.warning(f"Failed to add IP data to graph: {e}")
        
        clean_results = sanitize_for_json(results)
        return JSONResponse(content=clean_results)
        
    except Exception as e:
        logger.error(f"IP analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SpiderFoot OSINT Endpoints ====================

@app.get("/api/spiderfoot/health")
async def spiderfoot_health():
    """Check SpiderFoot availability"""
    is_healthy = spiderfoot_client.check_health()
    return {
        "available": is_healthy,
        "url": spiderfoot_client.base_url
    }

@app.post("/api/spiderfoot/scan/start")
async def start_spiderfoot_scan(target: str = Form(...), scan_name: str = Form(None)):
    """Start a new SpiderFoot scan"""
    try:
        logger.info(f"Starting SpiderFoot scan for: {target}")
        result = spiderfoot_client.start_scan(target, scan_name)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"SpiderFoot scan start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/spiderfoot/scan/status/{scan_id}")
async def get_spiderfoot_scan_status(scan_id: str):
    """Get status of a SpiderFoot scan"""
    try:
        status = spiderfoot_client.get_scan_status(scan_id)
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Failed to get scan status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/spiderfoot/scan/results/{scan_id}")
async def get_spiderfoot_scan_results(scan_id: str):
    """Get results from a completed scan"""
    try:
        results = spiderfoot_client.get_scan_results(scan_id)
        clean_results = sanitize_for_json(results)
        return JSONResponse(content=clean_results)
    except Exception as e:
        logger.error(f"Failed to get scan results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/spiderfoot/scans")
async def list_spiderfoot_scans():
    """List all SpiderFoot scans"""
    try:
        scans = spiderfoot_client.list_scans()
        return JSONResponse(content={"scans": scans})
    except Exception as e:
        logger.error(f"Failed to list scans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/spiderfoot/scan/{scan_id}")
async def delete_spiderfoot_scan(scan_id: str):
    """Delete a SpiderFoot scan"""
    try:
        success = spiderfoot_client.delete_scan(scan_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Failed to delete scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )