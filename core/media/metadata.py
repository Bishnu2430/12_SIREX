import subprocess
import json

class MetadataExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract(self):
        command = ["exiftool", "-j", self.file_path]

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)[0]
        except Exception as e:
            raise RuntimeError(f"Metadata extraction failed: {str(e)}")

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
