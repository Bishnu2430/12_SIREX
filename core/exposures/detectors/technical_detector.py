"""
Technical Exposure Detector
Detects API keys, credentials, IP addresses, secrets
"""

import re
import logging
from typing import List, Dict, Any
from ..models import Exposure, ExposureCategory, SeverityLevel

logger = logging.getLogger(__name__)


class TechnicalDetector:
    """Detects technical/security exposures"""
    
    # API Key patterns (provider-specific)
    API_KEY_PATTERNS = {
        'aws': re.compile(r'AKIA[0-9A-Z]{16}'),
        'google': re.compile(r'AIza[0-9A-Za-z\-_]{35}'),
        'github': re.compile(r'ghp_[0-9a-zA-Z]{36}'),
        'slack': re.compile(r'xox[baprs]-[0-9a-zA-Z-]{10,48}'),
        'stripe': re.compile(r'sk_live_[0-9a-zA-Z]{24}'),
    }
    
    # Generic secret patterns
    SECRET_PATTERNS = [
        re.compile(r'(?i)(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})'),
        re.compile(r'(?i)(secret|password|passwd|pwd)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-@!#$%^&*]{8,})'),
        re.compile(r'(?i)(token|auth)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})'),
    ]
    
    # IP Address patterns
    IPV4_PATTERN = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
    
    # Database connection strings
    DB_PATTERN = re.compile(r'(?i)(mongodb|mysql|postgres|postgresql)://[^\s]+')
    
    # Private key indicators
    PRIVATE_KEY_PATTERN = re.compile(r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----')
    
    def __init__(self):
        self.exposure_counter = 0
    
    def detect(self, signals: Dict[str, Any]) -> List[Exposure]:
        """Detect technical exposures from signals"""
        exposures = []
        
        # Collect all text sources
        text_content = self._collect_text(signals)
        
        # Check for API keys
        exposures.extend(self._check_api_keys(text_content))
        
        # Check for generic secrets
        exposures.extend(self._check_secrets(text_content))
        
        # Check for IP addresses
        exposures.extend(self._check_ip_addresses(text_content))
        
        # Check for database connections
        exposures.extend(self._check_db_connections(text_content))
        
        # Check for private keys
        exposures.extend(self._check_private_keys(text_content))
        
        logger.info(f"Technical detector found {len(exposures)} exposures")
        return exposures
    
    def _collect_text(self, signals: Dict[str, Any]) -> str:
        """Collect all text from various signal sources"""
        text_parts = []
        
        # OCR text
        if 'ocr' in signals:
            if isinstance(signals['ocr'], dict):
                text_parts.append(signals['ocr'].get('text', ''))
            elif isinstance(signals['ocr'], list):
                text_parts.extend([item.get('text', '') if isinstance(item, dict) else str(item) for item in signals['ocr']])
        
        # Transcription
        if 'transcription' in signals:
            if isinstance(signals['transcription'], str):
                text_parts.append(signals['transcription'])
            elif isinstance(signals['transcription'], dict):
                text_parts.append(signals['transcription'].get('text', ''))
        
        return ' '.join(text_parts)
    
    def _check_api_keys(self, text: str) -> List[Exposure]:
        """Check for provider-specific API keys"""
        exposures = []
        
        for provider, pattern in self.API_KEY_PATTERNS.items():
            matches = pattern.findall(text)
            for match in matches[:3]:  # Limit per provider
                self.exposure_counter += 1
                
                masked = match[:8] + "..." + match[-4:] if len(match) > 12 else match[:4] + "..."
                
                exposures.append(Exposure(
                    id=f"TECH-{self.exposure_counter:03d}",
                    category=ExposureCategory.TECHNICAL,
                    severity=SeverityLevel.CRITICAL,
                    title=f"{provider.upper()} API Key Exposed",
                    description=f"Active API key for {provider.capitalize()} found in content",
                    evidence={
                        "provider": provider,
                        "key_prefix": match[:8],
                        "masked_key": masked
                    },
                    risk_explanation=f"API key exposure - enables unauthorized access to {provider.capitalize()} resources, potential data breach or financial charges",
                    recommendations=[
                        f"IMMEDIATELY rotate this API key in {provider.capitalize()} console",
                        "Revoke the exposed key",
                        "Review access logs for unauthorized usage",
                        "Implement secret scanning in CI/CD pipeline",
                        "Use environment variables instead of hardcoding keys"
                    ],
                    confidence=0.95
                ))
        
        return exposures
    
    def _check_secrets(self, text: str) -> List[Exposure]:
        """Check for generic secrets and passwords"""
        exposures = []
        
        for pattern in self.SECRET_PATTERNS:
            matches = pattern.findall(text)
            for match in matches[:5]:  # Limit
                if isinstance(match, tuple) and len(match) >= 2:
                    secret_type = match[0]
                    secret_value = match[1]
                    
                    # Skip if looks like placeholder
                    if any(placeholder in secret_value.lower() for placeholder in ['example', 'your', 'xxx', '***']):
                        continue
                    
                    self.exposure_counter += 1
                    masked = secret_value[:3] + "***" + secret_value[-2:] if len(secret_value) > 5 else "***"
                    
                    exposures.append(Exposure(
                        id=f"TECH-{self.exposure_counter:03d}",
                        category=ExposureCategory.TECHNICAL,
                        severity=SeverityLevel.HIGH,
                        title=f"{secret_type.capitalize()} Exposed in Content",
                        description=f"Potential secret or credential found",
                        evidence={
                            "type": secret_type,
                            "masked_value": masked,
                            "length": len(secret_value)
                        },
                        risk_explanation="Credential exposure - may allow unauthorized system access",
                        recommendations=[
                            "Rotate this credential immediately",
                            "Remove sensitive data from shared content",
                            "Use secret management tools (HashiCorp Vault, AWS Secrets Manager)",
                            "Never commit secrets to version control"
                        ],
                        confidence=0.75
                    ))
        
        return exposures
    
    def _check_ip_addresses(self, text: str) -> List[Exposure]:
        """Check for IP addresses"""
        exposures = []
        ips = self.IPV4_PATTERN.findall(text)
        
        # Filter out common/localhost IPs
        filtered_ips = [ip for ip in ips if not ip.startswith(('127.', '0.0.0', '255.255'))]
        
        for ip in filtered_ips[:5]:  # Limit
            # Determine if private or public
            is_private = (
                ip.startswith('192.168.') or
                ip.startswith('10.') or
                ip.startswith('172.16.') or
                ip.startswith('172.17.') or
                ip.startswith('172.31.')
            )
            
            severity = SeverityLevel.LOW if is_private else SeverityLevel.MEDIUM
            
            self.exposure_counter += 1
            exposures.append(Exposure(
                id=f"TECH-{self.exposure_counter:03d}",
                category=ExposureCategory.TECHNICAL,
                severity=severity,
                title=f"{'Private' if is_private else 'Public'} IP Address Exposed",
                description=f"IP address found in content: {ip}",
                evidence={
                    "ip_address": ip,
                    "is_private": is_private
                },
                risk_explanation="IP exposure - reveals network infrastructure" + (
                    ", hosting provider, or personal connection" if not is_private else
                    ", internal network structure"
                ),
                recommendations=[
                    "Redact IP addresses from shared content",
                    "Use VPN or proxy for sensitive operations" if not is_private else "Avoid exposing internal network topology",
                    "Review firewall rules if internal IPs are exposed"
                ],
                confidence=0.9
            ))
        
        return exposures
    
    def _check_db_connections(self, text: str) -> List[Exposure]:
        """Check for database connection strings"""
        exposures = []
        connections = self.DB_PATTERN.findall(text)
        
        for conn in connections[:3]:  # Limit
            self.exposure_counter += 1
            
            # Mask the connection string
            masked = re.sub(r'://[^@]*@', '://***:***@', conn)
            
            exposures.append(Exposure(
                id=f"TECH-{self.exposure_counter:03d}",
                category=ExposureCategory.TECHNICAL,
                severity=SeverityLevel.CRITICAL,
                title="Database Connection String Exposed",
                description="Database credentials found in content",
                evidence={
                    "db_type": conn.split(':')[0],
                    "masked_connection": masked
                },
                risk_explanation="Database credential exposure - allows full database access, data exfiltration, or deletion",
                recommendations=[
                    "IMMEDIATELY rotate database credentials",
                    "Review database access logs",
                    "Use connection string encryption or secrets management",
                    "Implement IP whitelisting for database access",
                    "Never hardcode database credentials"
                ],
                confidence=0.95
            ))
        
        return exposures
    
    def _check_private_keys(self, text: str) -> List[Exposure]:
        """Check for private cryptographic keys"""
        exposures = []
        
        if self.PRIVATE_KEY_PATTERN.search(text):
            self.exposure_counter += 1
            
            exposures.append(Exposure(
                id=f"TECH-{self.exposure_counter:03d}",
                category=ExposureCategory.TECHNICAL,
                severity=SeverityLevel.CRITICAL,
                title="Private Cryptographic Key Exposed",
                description="Private key found in content (RSA/EC/SSH)",
                evidence={
                    "key_type": "Private Key (PEM format)",
                    "warning": "Full private key detected"
                },
                risk_explanation="Private key exposure - allows impersonation, unauthorized access, or decryption of sensitive data",
                recommendations=[
                    "IMMEDIATELY revoke and regenerate this key pair",
                    "Remove all copies of exposed key",
                    "Rotate any systems using this key",
                    "Review access logs for unauthorized usage",
                    "Use hardware security modules (HSM) or key management services"
                ],
                confidence=1.0
            ))
        
        return exposures
