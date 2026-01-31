import subprocess
import json
import shutil
import logging
import os

logger = logging.getLogger(__name__)

class MetadataExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract(self):
        metadata = {
            "exif": {},
            "streams": [],
            "format": {},
            "error": None
        }

        # 1. EXIFTOOL (Deep Metadata)
        if shutil.which("exiftool"):
            try:
                # -j for JSON, -g for group names, -struct to preserve structure
                command = ["exiftool", "-j", "-g", "-struct", self.file_path]
                result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.returncode == 0:
                    metadata["exif"] = json.loads(result.stdout)[0]
            except Exception as e:
                logger.warning(f"Exiftool extraction failed: {e}")
        else:
             logger.warning("Exiftool not found in PATH.")

        # 2. FFPROBE (Stream Details)
        if shutil.which("ffprobe"):
            try:
                command = [
                    "ffprobe", 
                    "-v", "quiet", 
                    "-print_format", "json", 
                    "-show_format", 
                    "-show_streams", 
                    self.file_path
                ]
                result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.returncode == 0:
                    ff_data = json.loads(result.stdout)
                    metadata["streams"] = ff_data.get("streams", [])
                    metadata["format"] = ff_data.get("format", {})
            except Exception as e:
                logger.warning(f"FFprobe extraction failed: {e}")
        else:
            logger.warning("FFprobe not found in PATH.")

        # Flatten critical fields for easy access, but keep full 'exif' and 'streams' for UI
        flat_data = {
            "timestamp": self._get_timestamp(metadata),
            "device_make": metadata["exif"].get("EXIF", {}).get("Make") or metadata["exif"].get("QuickTime", {}).get("Make"),
            "device_model": metadata["exif"].get("EXIF", {}).get("Model") or metadata["exif"].get("QuickTime", {}).get("Model"),
            "gps_latitude": metadata["exif"].get("Composite", {}).get("GPSLatitude"),
            "gps_longitude": metadata["exif"].get("Composite", {}).get("GPSLongitude"),
            "duration": metadata["format"].get("duration"),
            "full_metadata": metadata # Store everything here
        }
        
        return flat_data

    def _get_timestamp(self, meta):
        # Try various common date fields
        exif = meta.get("exif", {})
        return (
            exif.get("EXIF", {}).get("DateTimeOriginal") or 
            exif.get("QuickTime", {}).get("CreateDate") or 
            exif.get("File", {}).get("FileModifyDate")
        )