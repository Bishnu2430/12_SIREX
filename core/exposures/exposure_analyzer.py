"""
Exposure Analyzer
Main orchestrator for exposure detection
"""

import logging
from typing import Dict, Any
from .models import ExposureReport
from .detectors import LocationDetector, IdentityDetector, TechnicalDetector

logger = logging.getLogger(__name__)


class ExposureAnalyzer:
    """Main exposure analysis orchestrator"""
    
    def __init__(self):
        """Initialize all detectors"""
        self.location_detector = LocationDetector()
        self.identity_detector = IdentityDetector()
        self.technical_detector = TechnicalDetector()
        logger.info("Exposure Analyzer initialized with 3 detectors")
    
    def analyze(self, signals: Dict[str, Any]) -> ExposureReport:
        """
        Run all exposure detectors and generate comprehensive report
        
        Args:
            signals: Dictionary containing extracted signals from media
                     (metadata, ocr, transcription, faces, objects, etc.)
        
        Returns:
            ExposureReport with all detected exposures and summary
        """
        logger.info("Starting exposure analysis")
        all_exposures = []
        
        try:
            # Run location detection
            location_exposures = self.location_detector.detect(signals)
            all_exposures.extend(location_exposures)
            logger.debug(f"Found {len(location_exposures)} location exposures")
        except Exception as e:
            logger.error(f"Location detection failed: {e}")
        
        try:
            # Run identity detection
            identity_exposures = self.identity_detector.detect(signals)
            all_exposures.extend(identity_exposures)
            logger.debug(f"Found {len(identity_exposures)} identity exposures")
        except Exception as e:
            logger.error(f"Identity detection failed: {e}")
        
        try:
            # Run technical detection
            technical_exposures = self.technical_detector.detect(signals)
            all_exposures.extend(technical_exposures)
            logger.debug(f"Found {len(technical_exposures)} technical exposures")
        except Exception as e:
            logger.error(f"Technical detection failed: {e}")
        
        # Create comprehensive report
        report = ExposureReport(exposures=all_exposures)
        
        logger.info(f"Exposure analysis complete: {report.total_count} exposures found")
        logger.info(f"Severity breakdown: {report.by_severity}")
        
        return report
