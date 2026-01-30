import os
import mimetypes
from datetime import datetime

SUPPORTED_IMAGE = ["image/jpeg", "image/png", "image/jpg"]
SUPPORTED_VIDEO = ["video/mp4", "video/mov", "video/avi", "video/mkv"]
SUPPORTED_AUDIO = ["audio/wav", "audio/mp3", "audio/mpeg"]

class MediaIntake:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.media_type = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.working_dir = os.path.join("storage", "sessions", self.session_id)

    def detect_media_type(self):
        mime_type, _ = mimetypes.guess_type(self.file_path)

        if mime_type in SUPPORTED_IMAGE:
            self.media_type = "image"
        elif mime_type in SUPPORTED_VIDEO:
            self.media_type = "video"
        elif mime_type in SUPPORTED_AUDIO:
            self.media_type = "audio"
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

        return self.media_type

    def prepare_workspace(self):
        os.makedirs(self.working_dir, exist_ok=True)
        return self.working_dir

    def process(self):
        media_type = self.detect_media_type()
        workspace = self.prepare_workspace()

        return {
            "file_path": self.file_path,
            "media_type": media_type,
            "workspace": workspace,
            "session_id": self.session_id
        }
