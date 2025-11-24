import os
from pathlib import Path
from typing import List, Tuple

VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

def get_media_files(directory: str) -> Tuple[List[str], List[str]]:
    """
    Scans the directory for video and image files.
    Returns a tuple: (video_paths, image_paths)
    """
    video_files = []
    image_files = []
    
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    for file in path.rglob('*'):
        if file.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append(str(file.absolute()))
        elif file.suffix.lower() in IMAGE_EXTENSIONS:
            image_files.append(str(file.absolute()))
            
    # Sort by creation time
    video_files.sort(key=lambda x: os.path.getctime(x))
    image_files.sort(key=lambda x: os.path.getctime(x))
            
    return video_files, image_files
