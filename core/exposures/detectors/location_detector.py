"""
Location Exposure Detector
Detects GPS coordinates, addresses, and location mentions
"""

import re
import logging
from typing import List, Dict, Any
from ..models import Exposure, ExposureCategory, SeverityLevel

logger = logging.getLogger(__name__)


class LocationDetector:
    """Detects location-based exposures"""
    
    # GPS coordinate patterns
    GPS_PATTERN = re.compile(
        r'(-?\d{1,3}\.\d+)[,\s]+(-?\d{1,3}\.\d+)'
    )
    
    # Address patterns (simplified)
    ADDRESS_PATTERNS = [
        re.compile(r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|lane|ln|way|court|ct|circle|cir)', re.IGNORECASE),
        re.compile(r'P\.?O\.?\s+Box\s+\d+', re.IGNORECASE),
    ]
    
    def __init__(self):
        self.exposure_counter = 0
    
    def detect(self, signals: Dict[str, Any]) -> List[Exposure]:
        """Detect location exposures from signals"""
        exposures = []
        
        # Check EXIF metadata for GPS
        if 'metadata' in signals:
            exposures.extend(self._check_exif_gps(signals['metadata']))
        
        # Check OCR text for addresses
        if 'ocr' in signals:
            exposures.extend(self._check_text_addresses(signals['ocr']))
        
        # Check transcription for location mentions
        if 'transcription' in signals:
            exposures.extend(self._check_text_addresses(signals['transcription']))
        
        logger.info(f"Location detector found {len(exposures)} exposures")
        return exposures
    
    def _check_exif_gps(self, metadata: Dict[str, Any]) -> List[Exposure]:
        """Check EXIF data for GPS coordinates"""
        exposures = []
        
        # Check for GPS in metadata dict
        gps_data = metadata.get('gps', {})
        if not gps_data:
            return exposures
        
        latitude = gps_data.get('latitude') or gps_data.get('GPSLatitude')
        longitude = gps_data.get('longitude') or gps_data.get('GPSLongitude')
        
        if latitude and longitude:
            self.exposure_counter += 1
            
            exposures.append(Exposure(
                id=f"LOC-{self.exposure_counter:03d}",
                category=ExposureCategory.LOCATION,
                severity=SeverityLevel.HIGH,
                title="GPS Coordinates in Image Metadata",
                description=f"Exact GPS location embedded in image EXIF data",
                evidence={
                    "latitude": latitude,
                    "longitude": longitude,
                    "source": "EXIF metadata"
                },
                risk_explanation="Physical location exposure - enables stalking, doxxing, or revealing home/work address",
                recommendations=[
                    "Strip EXIF metadata before sharing: exiftool -all= image.jpg",
                    "Use photo editing tools that remove metadata by default",
                    "Disable location services in camera app if not needed"
                ],
                confidence=1.0
            ))
        
        return exposures
    
    def _check_text_addresses(self, text_data: Any) -> List[Exposure]:
        """Check text for physical addresses"""
        exposures = []
        
        # Handle different text formats
        if isinstance(text_data, dict):
            text = text_data.get('text', '')
        elif isinstance(text_data, list):
            # Combine OCR results
            text = ' '.join([item.get('text', '') if isinstance(item, dict) else str(item) for item in text_data])
        else:
            text = str(text_data)
        
        if not text:
            return exposures
        
        # Check for address patterns
        for pattern in self.ADDRESS_PATTERNS:
            matches = pattern.findall(text)
            for match in matches[:3]:  # Limit to first 3 to avoid spam
                self.exposure_counter += 1
                
                exposures.append(Exposure(
                    id=f"LOC-{self.exposure_counter:03d}",
                    category=ExposureCategory.LOCATION,
                    severity=SeverityLevel.MEDIUM,
                    title="Physical Address Detected",
                    description=f"Address found in text content",
                    evidence={
                        "address": match,
                        "source": "OCR/Transcription"
                    },
                    risk_explanation="Physical address exposure - may reveal home, work, or personal locations",
                    recommendations=[
                        "Redact addresses from shared documents",
                        "Use generic location descriptions instead of specific addresses",
                        "Blur or crop out address information from images"
                    ],
                    confidence=0.8
                ))
        
        return exposures
