import cv2
import os

class FrameExtractor:
    def __init__(self, video_path: str, workspace: str, interval_sec: int = 2):
        self.video_path = video_path
        self.workspace = os.path.abspath(workspace)
        self.interval_sec = interval_sec
        self.frames_dir = os.path.join(self.workspace, "frames")
        os.makedirs(self.frames_dir, exist_ok=True)

        if os.path.isabs(self.video_path):
            self.video_full_path = self.video_path
        else:
            candidate_in_workspace = os.path.join(self.workspace, self.video_path)
            if os.path.exists(candidate_in_workspace):
                self.video_full_path = os.path.abspath(candidate_in_workspace)
            else:
                self.video_full_path = os.path.abspath(self.video_path)

    def extract(self):
        cap = cv2.VideoCapture(self.video_full_path)

        if not cap.isOpened():
            raise RuntimeError(f"Unable to open video file: {self.video_full_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30  # default
        frame_interval = int(fps * self.interval_sec)

        frames_metadata = []
        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % max(frame_interval, 1) == 0:
                timestamp = frame_count / fps
                frame_name = f"frame_{saved_count:04d}.jpg"
                frame_path = os.path.join(self.frames_dir, frame_name)

                cv2.imwrite(frame_path, frame)

                frames_metadata.append({
                    "frame_id": saved_count,
                    "path": frame_path,
                    "timestamp_sec": round(timestamp, 2)
                })

                saved_count += 1

            frame_count += 1

        cap.release()

        return {
            "total_frames_extracted": saved_count,
            "frames_dir": self.frames_dir,
            "frames": frames_metadata
        }