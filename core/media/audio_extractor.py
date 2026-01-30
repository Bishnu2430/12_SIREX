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

        # locate ffmpeg executable
        ffmpeg_exe = shutil.which("ffmpeg")
        if not ffmpeg_exe:
            raise RuntimeError(
                "ffmpeg not found in PATH. Install ffmpeg or add it to PATH. "
                "On Windows you can download from https://ffmpeg.org/download.html"
            )

        command = [
            ffmpeg_exe,
            "-i", self.video_path,
            "-vn",              # no video
            "-acodec", "pcm_s16le",
            "-ar", "16000",     # 16kHz for ML models
            "-ac", "1",         # mono channel
            output_audio_path,
            "-y"                # overwrite
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Audio extraction failed: {e.stderr.decode()}")

        return {
            "audio_path": output_audio_path
        }
