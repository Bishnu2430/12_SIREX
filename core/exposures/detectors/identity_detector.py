"""
Identity Exposure Detector
Detects PII, emails, phone numbers, names, etc.
"""

import re
import logging
from typing import List, Dict, Any
from ..models import Exposure, ExposureCategory, SeverityLevel

logger = logging.getLogger(__name__)


class IdentityDetector:
    """Detects identity-based exposures"""
    
    # Email pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Phone patterns (US focused, can expand)
    PHONE_PATTERNS = [
        re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),
        re.compile(r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'),
    ]
    
    # SSN pattern
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    
    # Credit card pattern (simple)
    CC_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
    
    # Personal email indicators
    PERSONAL_EMAIL_DOMAINS = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'icloud.com', 'protonmail.com', 'aol.com'
    ]
    
    def __init__(self):
        self.exposure_counter = 0
    
    def detect(self, signals: Dict[str, Any]) -> List[Exposure]:
        """Detect identity exposures from signals"""
        exposures = []
        
        # Collect all text sources
        text_content = self._collect_text(signals)
        
        # Check for emails
        exposures.extend(self._check_emails(text_content))
        
        # Check for phone numbers
        exposures.extend(self._check_phones(text_content))
        
        # Check for SSN
        exposures.extend(self._check_ssn(text_content))
        
        # Check for credit cards
        exposures.extend(self._check_credit_cards(text_content))
        
        # Check metadata for author/creator names
        if 'metadata' in signals:
            exposures.extend(self._check_metadata_identity(signals['metadata']))
        
        logger.info(f"Identity detector found {len(exposures)} exposures")
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
    
    def _check_emails(self, text: str) -> List[Exposure]:
        """Check for email addresses"""
        exposures = []
        emails = self.EMAIL_PATTERN.findall(text)
        
        for email in emails[:5]:  # Limit to avoid spam
            # Determine if personal or work email
            domain = email.split('@')[1].lower()
            is_personal = domain in self.PERSONAL_EMAIL_DOMAINS
            
            severity = SeverityLevel.MEDIUM if is_personal else SeverityLevel.LOW
            
            self.exposure_counter += 1
            exposures.append(Exposure(
                id=f"ID-{self.exposure_counter:03d}",
                category=ExposureCategory.IDENTITY,
                severity=severity,
                title=f"{'Personal' if is_personal else 'Work'} Email Address Exposed",
                description=f"Email address found in content: {email[:3]}...@{domain}",
                evidence={
                    "email": email,
                    "domain": domain,
                    "is_personal": is_personal
                },
                risk_explanation="Email exposure - enables spam, phishing, identity correlation" + (
                    " (personal email may reveal real identity)" if is_personal else ""
                ),
                recommendations=[
                    "Redact email addresses from shared content",
                    "Use alias emails for public communications" if is_personal else "Use official contact forms instead of direct emails",
                    "Enable spam filtering and 2FA on email account"
                ],
                confidence=0.95
            ))
        
        return exposures
    
    def _check_phones(self, text: str) -> List[Exposure]:
        """Check for phone numbers"""
        exposures = []
        
        for pattern in self.PHONE_PATTERNS:
            phones = pattern.findall(text)
            for phone in phones[:3]:  # Limit
                self.exposure_counter += 1
                
                exposures.append(Exposure(
                    id=f"ID-{self.exposure_counter:03d}",
                    category=ExposureCategory.IDENTITY,
                    severity=SeverityLevel.MEDIUM,
                    title="Phone Number Detected",
                    description=f"Phone number found in content",
                    evidence={
                        "phone": phone,
                        "masked": phone[:3] + "-***-****"
                    },
                    risk_explanation="Phone number exposure - enables harassment, spam calls, SIM swapping attacks",
                    recommendations=[
                        "Redact phone numbers from public documents",
                        "Use business numbers or contact forms instead",
                        "Enable carrier-level spam protection"
                    ],
                    confidence=0.9
                ))
        
        return exposures
    
    def _check_ssn(self, text: str) -> List[Exposure]:
        """Check for Social Security Numbers"""
        exposures = []
        ssns = self.SSN_PATTERN.findall(text)
        
        for ssn in ssns[:2]:  # Critical, limit strictly
            self.exposure_counter += 1
            
            exposures.append(Exposure(
                id=f"ID-{self.exposure_counter:03d}",
                category=ExposureCategory.IDENTITY,
                severity=SeverityLevel.CRITICAL,
                title="Social Security Number Detected",
                description="SSN pattern found in content - CRITICAL SECURITY RISK",
                evidence={
                    "pattern_match": "XXX-XX-" + ssn[-4:],
                    "full_masked": "***-**-" + ssn[-4:]
                },
                risk_explanation="SSN exposure - enables identity theft, financial fraud, credit abuse",
                recommendations=[
                    "IMMEDIATELY redact/delete this content",
                    "Contact credit bureaus to place fraud alert",
                    "Monitor credit reports for unauthorized activity",
                    "Consider identity theft protection service"
                ],
                confidence=1.0
            ))
        
        return exposures
    
    def _check_credit_cards(self, text: str) -> List[Exposure]:
        """Check for credit card numbers"""
        exposures = []
        cards = self.CC_PATTERN.findall(text)
        
        for card in cards[:2]:  # Critical, limit strictly
            # Basic validation (could add Luhn algorithm)
            digits = re.sub(r'[\s-]', '', card)
            if len(digits) == 16:
                self.exposure_counter += 1
                
                exposures.append(Exposure(
                    id=f"ID-{self.exposure_counter:03d}",
                    category=ExposureCategory.IDENTITY,
                    severity=SeverityLevel.CRITICAL,
                    title="Credit Card Number Detected",
                    description="Potential credit card number found in content",
                    evidence={
                        "last_four": digits[-4:],
                        "masked": "**** **** **** " + digits[-4:]
                    },
                    risk_explanation="Credit card exposure - enables financial fraud, unauthorized charges",
                    recommendations=[
                        "IMMEDIATELY redact/delete this content",
                        "Report card as compromised to issuer",
                        "Request new card number",
                        "Monitor account for fraudulent transactions"
                    ],
                    confidence=0.85
                ))
        
        return exposures
    
    def _check_metadata_identity(self, metadata: Dict[str, Any]) -> List[Exposure]:
        """Check metadata for identity information"""
        exposures = []
        
        # Check for author/creator names
        author = metadata.get('author') or metadata.get('creator') or metadata.get('Artist')
        if author and len(author) > 3:
            self.exposure_counter += 1
            
            exposures.append(Exposure(
                id=f"ID-{self.exposure_counter:03d}",
                category=ExposureCategory.IDENTITY,
                severity=SeverityLevel.LOW,
                title="Author Name in Metadata",
                description=f"Creator name embedded in file metadata: {author}",
                evidence={
                    "author": author,
                    "source": "File metadata"
                },
                risk_explanation="Metadata identity exposure - may reveal real name when pseudonym is used",
                recommendations=[
                    "Strip metadata before sharing: exiftool -all= file.jpg",
                    "Use anonymous author names in document properties",
                    "Export files without metadata where possible"
                ],
                confidence=0.9
            ))
        
        return exposures
