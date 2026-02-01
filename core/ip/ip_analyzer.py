"""
Comprehensive IP Address OSINT Analyzer
Extracts geolocation, network intelligence, and threat information from IP addresses
"""

import requests
import socket
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import re


class IPAnalyzer:
    """
    Comprehensive IP OSINT Analysis
    
    Features:
    - IP geolocation (country, city, coordinates)
    - Network intelligence (ISP, ASN, organization)
    - Security analysis (VPN/proxy/Tor detection)
    - Reverse DNS lookup
    - Threat intelligence (optional with API key)
    - IP reputation checking
    """
    
    def __init__(self, abuseipdb_key: Optional[str] = None):
        self.abuseipdb_key = abuseipdb_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OSINT-Platform/1.0'
        })
    
    def analyze_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Comprehensive IP analysis
        
        Args:
            ip_address: IPv4 or IPv6 address
        
        Returns:
            Complete intelligence report
        """
        logger.info(f"Starting IP OSINT analysis for: {ip_address}")
        
        # Validate IP
        if not self._validate_ip(ip_address):
            return {
                "ip": ip_address,
                "error": "Invalid IP address format"
            }
        
        results = {
            "ip": ip_address,
            "analysis_timestamp": datetime.now().isoformat(),
            "geolocation": {},
            "network": {},
            "security": {},
            "dns": {},
            "threat_intelligence": {},
            "exposures": [],
            "intelligence_summary": {}
        }
        
        try:
            # Step 1: Geolocation analysis (ip-api.com - free, no key)
            results["geolocation"] = self._get_geolocation(ip_address)
            
            # Step 2: Enhanced network info (ipapi.co - free tier)
            enhanced_data = self._get_enhanced_data(ip_address)
            results["network"] = enhanced_data.get("network", {})
            results["security"] = enhanced_data.get("security", {})
            
            # Step 3: Reverse DNS lookup
            results["dns"] = self._reverse_dns_lookup(ip_address)
            
            # Step 4: Threat intelligence (if API key available)
            if self.abuseipdb_key:
                results["threat_intelligence"] = self._get_threat_intel(ip_address)
            else:
                results["threat_intelligence"] = {"message": "AbuseIPDB API key not configured"}
            
            # Step 5: Exposure detection
            results["exposures"] = self._detect_exposures(ip_address, results)
            
            # Step 6: Intelligence summary
            results["intelligence_summary"] = self._create_intelligence_summary(results)
            
            logger.success(f"✓ IP analysis completed for {ip_address}")
            
        except Exception as e:
            logger.error(f"IP analysis failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        
        if re.match(ipv4_pattern, ip):
            # Validate octets are 0-255
            octets = ip.split('.')
            return all(0 <= int(octet) <= 255 for octet in octets)
        elif re.match(ipv6_pattern, ip):
            return True
        
        return False
    
    def _get_geolocation(self, ip: str) -> Dict[str, Any]:
        """Get geolocation data from ip-api.com (free, no key required)"""
        logger.info(f"Fetching geolocation for {ip}")
        
        try:
            url = f"http://ip-api.com/json/{ip}"
            params = {
                "fields": "status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    return {
                        "location": {
                            "continent": data.get('continent'),
                            "country": data.get('country'),
                            "country_code": data.get('countryCode'),
                            "region": data.get('regionName'),
                            "city": data.get('city'),
                            "district": data.get('district'),
                            "postal_code": data.get('zip')
                        },
                        "coordinates": {
                            "latitude": data.get('lat'),
                            "longitude": data.get('lon')
                        },
                        "timezone": {
                            "name": data.get('timezone'),
                            "offset": data.get('offset'),
                            "currency": data.get('currency')
                        },
                        "network": {
                            "isp": data.get('isp'),
                            "organization": data.get('org'),
                            "as": data.get('as'),
                            "as_name": data.get('asname')
                        },
                        "flags": {
                            "mobile": data.get('mobile', False),
                            "proxy": data.get('proxy', False),
                            "hosting": data.get('hosting', False)
                        }
                    }
                else:
                    return {"error": data.get('message', 'Unknown error')}
            else:
                return {"error": f"API returned status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Geolocation lookup failed: {e}")
            return {"error": str(e)}
    
    def _get_enhanced_data(self, ip: str) -> Dict[str, Any]:
        """Get enhanced data from ipapi.co (free tier, 1000/day)"""
        logger.info(f"Fetching enhanced data for {ip}")
        
        try:
            url = f"https://ipapi.co/{ip}/json/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "network": {
                        "asn": data.get('asn'),
                        "network": data.get('network'),
                        "version": data.get('version'),
                        "org_name": data.get('org')
                    },
                    "security": {
                        "threat_level": self._assess_threat_level(data),
                        "is_datacenter": self._is_datacenter(data.get('org', '')),
                        "is_cloud_provider": self._is_cloud_provider(data.get('org', ''))
                    }
                }
            else:
                return {"error": f"Enhanced API returned {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Enhanced data lookup failed: {e}")
            return {"error": str(e)}
    
    def _reverse_dns_lookup(self, ip: str) -> Dict[str, Any]:
        """Perform reverse DNS lookup"""
        logger.info(f"Performing reverse DNS for {ip}")
        
        try:
            hostname = socket.gethostbyaddr(ip)
            return {
                "hostname": hostname[0],
                "aliases": hostname[1] if hostname[1] else [],
                "success": True
            }
        except socket.herror:
            return {
                "hostname": None,
                "success": False,
                "message": "No reverse DNS record found"
            }
        except Exception as e:
            return {
                "hostname": None,
                "success": False,
                "error": str(e)
            }
    
    def _get_threat_intel(self, ip: str) -> Dict[str, Any]:
        """Get threat intelligence from AbuseIPDB (requires API key)"""
        if not self.abuseipdb_key:
            return {"error": "AbuseIPDB API key not configured"}
        
        logger.info(f"Fetching threat intelligence for {ip}")
        
        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {
                "Key": self.abuseipdb_key,
                "Accept": "application/json"
            }
            params = {
                "ipAddress": ip,
                "maxAgeInDays": 90,
                "verbose": ""
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                
                return {
                    "abuse_confidence_score": data.get('abuseConfidenceScore', 0),
                    "is_whitelisted": data.get('isWhitelisted', False),
                    "total_reports": data.get('totalReports', 0),
                    "num_distinct_users": data.get('numDistinctUsers', 0),
                    "last_reported": data.get('lastReportedAt'),
                    "country_code": data.get('countryCode'),
                    "usage_type": data.get('usageType'),
                    "isp": data.get('isp'),
                    "domain": data.get('domain')
                }
            else:
                return {"error": f"AbuseIPDB API returned {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Threat intel lookup failed: {e}")
            return {"error": str(e)}
    
    def _detect_exposures(self, ip: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential exposure risks"""
        logger.info(f"Detecting exposures for {ip}")
        
        exposures = []
        geo = results.get("geolocation", {})
        security = results.get("security", {})
        threat = results.get("threat_intelligence", {})
        
        # VPN/Proxy detection
        if geo.get("flags", {}).get("proxy"):
            exposures.append({
                "type": "VPN/Proxy Detected",
                "severity": "MEDIUM",
                "description": "IP address is identified as a VPN or proxy",
                "value": "Proxy/VPN in use",
                "recommendation": "This may indicate anonymization attempts"
            })
        
        # Hosting/Datacenter detection
        if geo.get("flags", {}).get("hosting") or security.get("is_datacenter"):
            exposures.append({
                "type": "Hosting/Datacenter IP",
                "severity": "MEDIUM",
                "description": "IP belongs to a hosting provider or datacenter",
                "value": geo.get("network", {}).get("isp", "Unknown"),
                "recommendation": "May indicate automated activity or server-based access"
            })
        
        # Mobile detection
        if geo.get("flags", {}).get("mobile"):
            exposures.append({
                "type": "Mobile Network",
                "severity": "LOW",
                "description": "IP is from a mobile network",
                "value": "Mobile carrier",
                "recommendation": "User accessing from mobile device"
            })
        
        # Threat intelligence
        abuse_score = threat.get("abuse_confidence_score", 0)
        if abuse_score > 75:
            exposures.append({
                "type": "High Abuse Score",
                "severity": "CRITICAL",
                "description": "IP has high abuse confidence score",
                "value": f"{abuse_score}% abuse confidence",
                "recommendation": "IP has been reported for malicious activity"
            })
        elif abuse_score > 25:
            exposures.append({
                "type": "Moderate Abuse Score",
                "severity": "HIGH",
                "description": "IP has moderate abuse reports",
                "value": f"{abuse_score}% abuse confidence",
                "recommendation": "Exercise caution, IP has suspicious history"
            })
        
        # Cloud provider detection
        if security.get("is_cloud_provider"):
            exposures.append({
                "type": "Cloud Provider",
                "severity": "LOW",
                "description": "IP belongs to a major cloud provider",
                "value": geo.get("network", {}).get("org", "Cloud"),
                "recommendation": "May indicate cloud-based service or infrastructure"
            })
        
        return exposures
    
    def _create_intelligence_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive intelligence summary"""
        geo = results.get("geolocation", {})
        threat = results.get("threat_intelligence", {})
        security = results.get("security", {})
        dns = results.get("dns", {})
        
        location = geo.get("location", {})
        network = geo.get("network", {})
        flags = geo.get("flags", {})
        
        return {
            "ip_type": self._determine_ip_type(results),
            "geographic_location": f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}",
            "coordinates": geo.get("coordinates", {}),
            "isp": network.get("isp", "Unknown"),
            "organization": network.get("organization", "Unknown"),
            "asn": network.get("as", "Unknown"),
            "threat_level": self._calculate_threat_level(threat),
            "is_proxy_vpn": 1 if flags.get("proxy") else 0,
            "is_hosting": 1 if flags.get("hosting") else 0,
            "is_mobile": 1 if flags.get("mobile") else 0,
            "has_reverse_dns": 1 if dns.get("success") else 0,
            "hostname": dns.get("hostname"),
            "exposure_risk": self._calculate_exposure_risk(results.get("exposures", [])),
            "key_findings": self._extract_key_findings(results)
        }
    
    def _determine_ip_type(self, results: Dict) -> str:
        """Determine IP type"""
        flags = results.get("geolocation", {}).get("flags", {})
        security = results.get("security", {})
        
        if flags.get("proxy"):
            return "VPN/Proxy"
        elif flags.get("hosting") or security.get("is_datacenter"):
            return "Hosting/Datacenter"
        elif security.get("is_cloud_provider"):
            return "Cloud Provider"
        elif flags.get("mobile"):
            return "Mobile Network"
        else:
            return "Residential"
    
    def _assess_threat_level(self, data: Dict) -> str:
        """Assess basic threat level from network data"""
        return "Unknown"
    
    def _is_datacenter(self, org: str) -> bool:
        """Check if organization is a datacenter"""
        datacenter_keywords = ['datacenter', 'data center', 'hosting', 'server', 'cloud', 'digital ocean', 'linode', 'vultr']
        org_lower = org.lower()
        return any(keyword in org_lower for keyword in datacenter_keywords)
    
    def _is_cloud_provider(self, org: str) -> bool:
        """Check if organization is a major cloud provider"""
        cloud_providers = ['amazon', 'aws', 'google cloud', 'gcp', 'microsoft azure', 'azure', 'digitalocean', 'cloudflare']
        org_lower = org.lower()
        return any(provider in org_lower for provider in cloud_providers)
    
    def _calculate_threat_level(self, threat: Dict) -> str:
        """Calculate threat level"""
        abuse_score = threat.get("abuse_confidence_score", 0)
        
        if abuse_score > 75:
            return "CRITICAL"
        elif abuse_score > 50:
            return "HIGH"
        elif abuse_score > 25:
            return "MEDIUM"
        elif abuse_score > 0:
            return "LOW"
        else:
            return "CLEAN"
    
    def _calculate_exposure_risk(self, exposures: List) -> str:
        """Calculate overall exposure risk"""
        if not exposures:
            return "LOW"
        
        severity_levels = [e.get("severity", "LOW") for e in exposures]
        
        if "CRITICAL" in severity_levels:
            return "CRITICAL"
        elif "HIGH" in severity_levels:
            return "HIGH"
        elif "MEDIUM" in severity_levels:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_key_findings(self, results: Dict) -> List[str]:
        """Extract key intelligence findings"""
        findings = []
        
        geo = results.get("geolocation", {})
        threat = results.get("threat_intelligence", {})
        dns = results.get("dns", {})
        
        # Location
        location = geo.get("location", {})
        if location.get("city"):
            findings.append(f"Located in {location.get('city')}, {location.get('country')}")
        
        # Network
        network = geo.get("network", {})
        if network.get("isp"):
            findings.append(f"ISP: {network.get('isp')}")
        
        # Reverse DNS
        if dns.get("hostname"):
            findings.append(f"Hostname: {dns.get('hostname')}")
        
        # Flags
        flags = geo.get("flags", {})
        if flags.get("proxy"):
            findings.append("VPN/Proxy detected")
        if flags.get("hosting"):
            findings.append("Hosting/datacenter IP")
        if flags.get("mobile"):
            findings.append("Mobile network")
        
        # Threat intel
        total_reports = threat.get("total_reports", 0)
        if total_reports > 0:
            findings.append(f"Reported {total_reports} time(s) for abuse")
        
        return findings
