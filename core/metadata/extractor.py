"""
Comprehensive Metadata Extraction
Extracts EXIF, FFmpeg, and file-level metadata from images, videos, and audio
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import exifread
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import magic
from loguru import logger


class MetadataExtractor:
    """
    Extract maximum metadata from media files
    - EXIF data (images)
    - FFprobe data (videos/audio)
    - File properties
    - GPS coordinates
    - Camera/device information
    """
    
    def __init__(self):
        self.mime = magic.Magic(mime=True)
    
    def extract_all(self, file_path: str) -> Dict[str, Any]:
        """
        Extract ALL available metadata from a file
        
        Returns comprehensive metadata including:
        - File properties
        - EXIF data (images)
        - FFmpeg data (video/audio)
        - GPS coordinates
        - Device information
        - Technical specifications
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"error": "File not found"}
        
        metadata = {
            "file": self._extract_file_metadata(file_path),
            "mime_type": self._get_mime_type(file_path),
            "hash": self._calculate_hashes(file_path)
        }
        
        # Determine file type and extract appropriate metadata
        mime_type = metadata["mime_type"]
        
        if mime_type.startswith('image'):
            metadata["exif"] = self._extract_exif(file_path)
            metadata["image_properties"] = self._extract_image_properties(file_path)
            
        elif mime_type.startswith('video'):
            metadata["ffmpeg"] = self._extract_ffmpeg_metadata(file_path)
            metadata["video_properties"] = self._extract_video_properties(file_path)
            
        elif mime_type.startswith('audio'):
            metadata["ffmpeg"] = self._extract_ffmpeg_metadata(file_path)
            metadata["audio_properties"] = self._extract_audio_properties(file_path)
        
        # Extract GPS if available
        if "exif" in metadata:
            metadata["gps"] = self._extract_gps(metadata["exif"])
        
        # Extract camera/device info
        if "exif" in metadata:
            metadata["device"] = self._extract_device_info(metadata["exif"])
        
        return metadata
    
    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic file properties"""
        stat = file_path.stat()
        
        return {
            "name": file_path.name,
            "path": str(file_path.absolute()),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "extension": file_path.suffix.lower()
        }
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type"""
        try:
            return self.mime.from_file(str(file_path))
        except Exception as e:
            logger.warning(f"Failed to get MIME type: {e}")
            return "application/octet-stream"
    
    def _calculate_hashes(self, file_path: Path) -> Dict[str, str]:
        """Calculate file hashes for verification"""
        import hashlib
        
        hashes = {}
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                hashes["md5"] = hashlib.md5(data).hexdigest()
                hashes["sha1"] = hashlib.sha1(data).hexdigest()
                hashes["sha256"] = hashlib.sha256(data).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hashes: {e}")
        
        return hashes
    
    def _extract_exif(self, file_path: Path) -> Dict[str, Any]:
        """Extract EXIF data from images"""
        exif_data = {}
        
        try:
            # Method 1: Using exifread (more comprehensive)
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=True)
                
                for tag, value in tags.items():
                    if tag not in ['JPEGThumbnail', 'TIFFThumbnail', 'Filename']:
                        try:
                            exif_data[tag] = str(value)
                        except:
                            pass
            
            # Method 2: Using PIL (for GPS and standard tags)
            with Image.open(file_path) as img:
                exif = img.getexif()
                
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        # Handle GPS data specially
                        if tag == "GPSInfo":
                            gps_data = {}
                            for gps_tag_id, gps_value in value.items():
                                gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                gps_data[gps_tag] = str(gps_value)
                            exif_data["GPS_PIL"] = gps_data
                        else:
                            try:
                                exif_data[f"PIL_{tag}"] = str(value)
                            except:
                                pass
        
        except Exception as e:
            logger.warning(f"EXIF extraction failed: {e}")
        
        return exif_data
    
    def _extract_image_properties(self, file_path: Path) -> Dict[str, Any]:
        """Extract image-specific properties"""
        properties = {}
        
        try:
            with Image.open(file_path) as img:
                properties.update({
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "megapixels": round((img.width * img.height) / 1_000_000, 2),
                    "aspect_ratio": f"{img.width}:{img.height}",
                    "has_transparency": img.mode in ('RGBA', 'LA', 'P'),
                })
                
                # Get color profile
                if hasattr(img, 'info'):
                    properties["info"] = {k: str(v) for k, v in img.info.items() 
                                        if k not in ['exif', 'jfif']}
        
        except Exception as e:
            logger.warning(f"Failed to extract image properties: {e}")
        
        return properties
    
    def _extract_ffmpeg_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata using FFprobe (for video/audio)"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning(f"FFprobe failed: {result.stderr}")
                return {}
        
        except subprocess.TimeoutExpired:
            logger.error("FFprobe timeout")
            return {}
        except FileNotFoundError:
            logger.warning("FFprobe not installed")
            return {}
        except Exception as e:
            logger.error(f"FFprobe extraction failed: {e}")
            return {}
    
    def _extract_video_properties(self, file_path: Path) -> Dict[str, Any]:
        """Extract video-specific properties"""
        ffmpeg_data = self._extract_ffmpeg_metadata(file_path)
        properties = {}
        
        try:
            if 'format' in ffmpeg_data:
                fmt = ffmpeg_data['format']
                properties.update({
                    "duration_seconds": float(fmt.get('duration', 0)),
                    "bit_rate": int(fmt.get('bit_rate', 0)),
                    "format_name": fmt.get('format_name'),
                    "format_long_name": fmt.get('format_long_name'),
                })
            
            # Get video stream info
            if 'streams' in ffmpeg_data:
                for stream in ffmpeg_data['streams']:
                    if stream.get('codec_type') == 'video':
                        properties.update({
                            "codec": stream.get('codec_name'),
                            "codec_long_name": stream.get('codec_long_name'),
                            "width": stream.get('width'),
                            "height": stream.get('height'),
                            "fps": eval(stream.get('r_frame_rate', '0/1')),
                            "bit_rate": stream.get('bit_rate'),
                            "pixel_format": stream.get('pix_fmt'),
                            "color_space": stream.get('color_space'),
                        })
                        break
        
        except Exception as e:
            logger.warning(f"Failed to extract video properties: {e}")
        
        return properties
    
    def _extract_audio_properties(self, file_path: Path) -> Dict[str, Any]:
        """Extract audio-specific properties"""
        ffmpeg_data = self._extract_ffmpeg_metadata(file_path)
        properties = {}
        
        try:
            # Get audio stream info
            if 'streams' in ffmpeg_data:
                for stream in ffmpeg_data['streams']:
                    if stream.get('codec_type') == 'audio':
                        properties.update({
                            "codec": stream.get('codec_name'),
                            "sample_rate": int(stream.get('sample_rate', 0)),
                            "channels": stream.get('channels'),
                            "channel_layout": stream.get('channel_layout'),
                            "bit_rate": stream.get('bit_rate'),
                        })
                        break
            
            if 'format' in ffmpeg_data:
                properties["duration_seconds"] = float(ffmpeg_data['format'].get('duration', 0))
        
        except Exception as e:
            logger.warning(f"Failed to extract audio properties: {e}")
        
        return properties
    
    def _extract_gps(self, exif_data: Dict) -> Optional[Dict[str, Any]]:
        """Extract and parse GPS coordinates from EXIF"""
        gps = {}
        
        try:
            # Try to find GPS data in various formats
            lat_data = None
            lon_data = None
            
            # Check for exifread format
            if 'GPS GPSLatitude' in exif_data:
                lat_data = exif_data.get('GPS GPSLatitude')
                lat_ref = exif_data.get('GPS GPSLatitudeRef', 'N')
                lon_data = exif_data.get('GPS GPSLongitude')
                lon_ref = exif_data.get('GPS GPSLongitudeRef', 'E')
                
                if lat_data and lon_data:
                    # Parse coordinates
                    lat = self._parse_gps_coord(str(lat_data))
                    lon = self._parse_gps_coord(str(lon_data))
                    
                    if lat and lon:
                        if str(lat_ref) == 'S':
                            lat = -lat
                        if str(lon_ref) == 'W':
                            lon = -lon
                        
                        gps.update({
                            "latitude": lat,
                            "longitude": lon,
                            "location_string": f"{lat}, {lon}",
                            "google_maps_url": f"https://www.google.com/maps?q={lat},{lon}"
                        })
            
            # Add altitude if available
            if 'GPS GPSAltitude' in exif_data:
                alt = exif_data.get('GPS GPSAltitude')
                gps["altitude_meters"] = float(str(alt).split('/')[0])
            
            # Add timestamp if available
            if 'GPS GPSTimeStamp' in exif_data:
                gps["gps_timestamp"] = str(exif_data.get('GPS GPSTimeStamp'))
            
            if 'GPS GPSDateStamp' in exif_data:
                gps["gps_date"] = str(exif_data.get('GPS GPSDateStamp'))
        
        except Exception as e:
            logger.warning(f"GPS extraction failed: {e}")
        
        return gps if gps else None
    
    def _parse_gps_coord(self, coord_str: str) -> Optional[float]:
        """Parse GPS coordinate from EXIF format"""
        try:
            # Format: [degrees, minutes, seconds]
            coord_str = coord_str.strip('[]')
            parts = coord_str.split(',')
            
            if len(parts) >= 2:
                degrees = float(eval(parts[0].strip()))
                minutes = float(eval(parts[1].strip()))
                seconds = float(eval(parts[2].strip())) if len(parts) > 2 else 0
                
                return degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        except Exception as e:
            logger.debug(f"Failed to parse GPS coord: {e}")
        
        return None
    
    def _extract_device_info(self, exif_data: Dict) -> Dict[str, Any]:
        """Extract camera/device information"""
        device = {}
        
        # Camera make and model
        if 'Image Make' in exif_data:
            device["make"] = exif_data['Image Make']
        if 'Image Model' in exif_data:
            device["model"] = exif_data['Image Model']
        
        # Software
        if 'Image Software' in exif_data:
            device["software"] = exif_data['Image Software']
        
        # Camera settings
        if 'EXIF ISOSpeedRatings' in exif_data:
            device["iso"] = exif_data['EXIF ISOSpeedRatings']
        if 'EXIF FocalLength' in exif_data:
            device["focal_length"] = exif_data['EXIF FocalLength']
        if 'EXIF ExposureTime' in exif_data:
            device["exposure_time"] = exif_data['EXIF ExposureTime']
        if 'EXIF FNumber' in exif_data:
            device["f_number"] = exif_data['EXIF FNumber']
        
        # Lens information
        if 'EXIF LensModel' in exif_data:
            device["lens_model"] = exif_data['EXIF LensModel']
        
        return device if device else None