"""
SpiderFoot API Client
Integrates with SpiderFoot OSINT automation tool
"""

import requests
import time
from typing import Dict, Any, List, Optional
from loguru import logger


class SpiderFootClient:
    """
    Client for interacting with SpiderFoot API
    
    SpiderFoot provides 200+ OSINT modules for:
    - Domain/subdomain enumeration
    - Email harvesting
    - Social media profiling
    - Network reconnaissance
    - Threat intelligence
    """
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def check_health(self) -> bool:
        """Check if SpiderFoot is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"SpiderFoot health check failed: {e}")
            return False
    
    def start_scan(self, target: str, scan_name: Optional[str] = None, 
                   modules: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Start a new SpiderFoot scan
        
        Args:
            target: Target to scan (domain, IP, email, etc.)
            scan_name: Optional custom scan name
            modules: List of specific modules to use (default: all)
        
        Returns:
            Scan information including scan_id
        """
        try:
            if not scan_name:
                scan_name = f"scan_{target}_{int(time.time())}"
            
            # SpiderFoot API uses /api/scan
            payload = {
                "scanName": scan_name,
                "scanTarget": target,
                "moduleList": modules if modules else "",
                "typelist": ""
            }
            
            response = self.session.post(
                f"{self.base_url}/api/scan",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # API returns [scan_id] or {"id": scan_id}
                if isinstance(result, list) and len(result) > 0:
                    scan_id = result[0]
                else:
                    scan_id = result.get('id') if isinstance(result, dict) else str(result)
                
                logger.info(f"Started SpiderFoot scan: {scan_id} for {target}")
                
                return {
                    "success": True,
                    "scan_id": scan_id,
                    "scan_name": scan_name,
                    "target": target,
                    "message": "Scan started successfully"
                }
            else:
                error_msg = f"Failed to start scan: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                return {
                    "success": False,
                    "error": error_msg
                }
        
        except Exception as e:
            logger.error(f"Failed to start SpiderFoot scan: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """
        Get the status of a running scan
        
        Args:
            scan_id: The ID of the scan
        
        Returns:
            Scan status information
        """
        try:
            # Use the summary API endpoint
            response = self.session.get(
                f"{self.base_url}/api/scansummary",
                params={"id": scan_id},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"Failed to get status: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Failed to get scan status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        """
        Get results from a completed scan
        
        Args:
            scan_id: The ID of the scan
        
        Returns:
            Scan results
        """
        try:
            # Use scanresults endpoint
            response = self.session.get(
                f"{self.base_url}/api/scanresults",
                params={"id": scan_id},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Process and structure results
                return {
                    "success": True,
                    "scan_id": scan_id,
                    "results": data,
                    "total_events": len(data) if isinstance(data, list) else 0
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get results: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Failed to get scan results: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_scans(self) -> List[Dict[str, Any]]:
        """
        List all scans
        
        Returns:
            List of scan information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/scanlist",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to list scans: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Failed to list scans: {e}")
            return []
    
    def delete_scan(self, scan_id: str) -> bool:
        """
        Delete a scan
        
        Args:
            scan_id: The ID of the scan to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/scandelete",
                params={"id": scan_id},
                timeout=10
            )
            
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Failed to delete scan: {e}")
            return False
    
    def get_modules(self) -> List[Dict[str, Any]]:
        """
        Get list of available SpiderFoot modules
        
        Returns:
            List of module information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/modules",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
        
        except Exception as e:
            logger.error(f"Failed to get modules: {e}")
            return []
    
    def quick_scan(self, target: str, wait_for_completion: bool = False, 
                   timeout: int = 300) -> Dict[str, Any]:
        """
        Convenience method to start a scan and optionally wait for results
        
        Args:
            target: Target to scan
            wait_for_completion: If True, wait for scan to complete
            timeout: Maximum time to wait in seconds
        
        Returns:
            Scan results or status
        """
        # Start scan
        scan_info = self.start_scan(target)
        
        if not scan_info.get("success"):
            return scan_info
        
        scan_id = scan_info["scan_id"]
        
        if not wait_for_completion:
            return scan_info
        
        # Wait for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_scan_status(scan_id)
            
            if status.get("status") == "FINISHED":
                results = self.get_scan_results(scan_id)
                return results
            elif status.get("status") == "ERROR":
                return {
                    "success": False,
                    "error": "Scan failed"
                }
            
            time.sleep(5)  # Poll every 5 seconds
        
        return {
            "success": False,
            "error": "Scan timeout",
            "scan_id": scan_id,
            "message": "Scan is still running, check status later"
        }
