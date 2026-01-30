import os
import subprocess
import shutil

class AudioExtractor:
    def __init__(self, video_path: str, workspace: str):
        self.video_path = video_path
        self.workspace = workspace
        self.audio_dir = os.path.join(workspace, "audio")
        os.makedirs(self.audio_dir, exist_ok=True)

    def extract(self):
        output_audio_path = os.path.join(self.audio_dir, "extracted_audio.wav")

        ffmpeg_exe = shutil.which("ffmpeg")
        if not ffmpeg_exe:
            return {"audio_path": None}  # Skip if ffmpeg not available

        command = [
            ffmpeg_exe,
            "-i", self.video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_audio_path,
            "-y"
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return {"audio_path": None}

        return {"audio_path": output_audio_path}