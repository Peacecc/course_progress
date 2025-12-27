import os
from tinytag import TinyTag

class VideoScanner:
    VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v')

    @staticmethod
    def scan_directory(root_path):
        videos = []
        total_duration = 0
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.lower().endswith(VideoScanner.VIDEO_EXTENSIONS):
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, root_path)
                    duration = VideoScanner.get_duration(abs_path)
                    videos.append({
                        "rel_path": rel_path,
                        "abs_path": abs_path,
                        "duration": duration
                    })
                    total_duration += duration
        return videos, {"total_videos": len(videos), "total_duration": total_duration}

    @staticmethod
    def get_duration(file_path):
        try:
            tag = TinyTag.get(file_path)
            return tag.duration if tag.duration else 0
        except: return 0
