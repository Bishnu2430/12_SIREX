import subprocess
import json
import shutil

class MetadataExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract(self):
        if not shutil.which("exiftool"):
            return {
                "timestamp": None,
                "device_make": None,
                "device_model": None,
                "software": None,
                "gps_latitude": None,
                "gps_longitude": None,
                "gps_altitude": None
            }

        command = ["exiftool", "-j", self.file_path]

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)[0]
        except Exception:
            return {
                "timestamp": None,
                "device_make": None,
                "device_model": None,
                "software": None,
                "gps_latitude": None,
                "gps_longitude": None,
                "gps_altitude": None
            }

        parsed_data = {
            "timestamp": metadata.get("DateTimeOriginal") or metadata.get("CreateDate"),
            "device_make": metadata.get("Make"),
            "device_model": metadata.get("Model"),
            "software": metadata.get("Software"),
            "gps_latitude": metadata.get("GPSLatitude"),
            "gps_longitude": metadata.get("GPSLongitude"),
            "gps_altitude": metadata.get("GPSAltitude")
        }

        return parsed_data