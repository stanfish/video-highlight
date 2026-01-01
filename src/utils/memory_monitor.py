"""
Memory monitoring and estimation utilities for video processing.
Helps prevent out-of-memory crashes by estimating memory requirements
and checking available system memory.
"""

import os
import psutil
import subprocess
import json
from typing import List, Tuple, Dict
from pathlib import Path


def get_available_memory() -> int:
    """
    Get available system memory in bytes.
    
    Returns:
        int: Available memory in bytes
    """
    return psutil.virtual_memory().available


def get_total_memory() -> int:
    """
    Get total system memory in bytes.
    
    Returns:
        int: Total memory in bytes
    """
    return psutil.virtual_memory().total


def format_memory_size(bytes_size: int) -> str:
    """
    Format bytes to human-readable format (KB, MB, GB).
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        str: Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def get_video_info(video_path: str) -> Dict:
    """
    Get video metadata using ffprobe.
    
    Args:
        video_path: Path to video file
        
    Returns:
        dict: Video metadata including width, height, duration, fps
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None
            
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return None
        
        return {
            'width': int(video_stream.get('width', 1920)),
            'height': int(video_stream.get('height', 1080)),
            'duration': float(data.get('format', {}).get('duration', 0)),
            'fps': eval(video_stream.get('r_frame_rate', '30/1')),  # e.g., "30/1" -> 30.0
            'codec': video_stream.get('codec_name', 'unknown')
        }
    except Exception as e:
        print(f"Warning: Could not get video info for {video_path}: {e}")
        return None


def estimate_video_memory(video_path: str, target_width: int = 1920) -> int:
    """
    Estimate memory needed to load a video clip in MoviePy.
    
    This is an approximation based on:
    - Video resolution (resized to target_width)
    - Duration
    - Frame rate
    - Uncompressed frame size in memory
    
    Args:
        video_path: Path to video file
        target_width: Target width for processing (default: 1920)
        
    Returns:
        int: Estimated memory in bytes
    """
    info = get_video_info(video_path)
    
    if not info:
        # Fallback estimation for unknown videos
        # Assume 1080p, 30fps, 10 seconds
        return estimate_clip_memory(1920, 1080, 10.0, 30)
    
    # Calculate target height maintaining aspect ratio
    aspect_ratio = info['width'] / info['height']
    target_height = int(target_width / aspect_ratio)
    
    return estimate_clip_memory(target_width, target_height, info['duration'], info['fps'])


def estimate_image_memory(image_path: str, duration: float = 5.0, target_width: int = 1920) -> int:
    """
    Estimate memory needed for an image clip.
    
    Args:
        image_path: Path to image file
        duration: Duration the image will be displayed
        target_width: Target width for processing
        
    Returns:
        int: Estimated memory in bytes
    """
    try:
        from PIL import Image
        img = Image.open(image_path)
        width, height = img.size
        
        # Calculate target height maintaining aspect ratio
        aspect_ratio = width / height
        target_height = int(target_width / aspect_ratio)
        
        # Images in MoviePy are simpler - just one frame repeated
        # But we still need to account for processing overhead
        return estimate_clip_memory(target_width, target_height, duration, 1)
    except Exception as e:
        print(f"Warning: Could not get image info for {image_path}: {e}")
        # Fallback: assume standard photo
        return estimate_clip_memory(1920, 1080, duration, 1)


def estimate_clip_memory(width: int, height: int, duration: float, fps: float) -> int:
    """
    Estimate memory for a video clip based on dimensions and duration.
    
    MoviePy keeps frames in memory as numpy arrays (RGB, 8-bit per channel).
    Memory = width * height * 3 (RGB) * number_of_frames
    
    We add overhead for:
    - MoviePy internal structures (~20%)
    - Processing buffers (~30%)
    - Resizing operations (~50% extra during processing)
    
    Args:
        width: Video width in pixels
        height: Video height in pixels
        duration: Duration in seconds
        fps: Frames per second
        
    Returns:
        int: Estimated memory in bytes
    """
    # Base memory: uncompressed RGB frames
    bytes_per_pixel = 3  # RGB
    num_frames = int(duration * fps)
    
    # MoviePy doesn't load all frames at once, but keeps a buffer
    # Estimate ~2 seconds of frames in memory at a time
    buffer_frames = min(num_frames, int(2 * fps))
    
    base_memory = width * height * bytes_per_pixel * buffer_frames
    
    # Add overhead (2x for safety margin during processing)
    total_memory = base_memory * 2
    
    return int(total_memory)


def estimate_total_memory(media_files: List[str], target_width: int = 1920, 
                         clip_duration: float = 5.0) -> Dict:
    """
    Estimate total memory needed to process all media files.
    
    Args:
        media_files: List of media file paths
        target_width: Target width for processing
        clip_duration: Average duration per clip
        
    Returns:
        dict: {
            'total_estimated': total memory needed in bytes,
            'per_file': list of (filename, estimated_memory) tuples,
            'peak_memory': estimated peak memory usage
        }
    """
    per_file = []
    total = 0
    
    for media_path in media_files:
        ext = os.path.splitext(media_path)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            estimated = estimate_image_memory(media_path, clip_duration, target_width)
        else:
            estimated = estimate_video_memory(media_path, target_width)
        
        per_file.append((os.path.basename(media_path), estimated))
        total += estimated
    
    # Peak memory is when we have all clips loaded + assembly overhead
    # During assembly, we also create resized versions
    peak_memory = total * 1.5  # 50% overhead for assembly
    
    # Add base overhead for Python, libraries, AI model
    base_overhead = 2 * 1024 * 1024 * 1024  # 2 GB base
    
    return {
        'total_estimated': int(total),
        'per_file': per_file,
        'peak_memory': int(peak_memory + base_overhead)
    }


def check_memory_safety(estimated_memory: int, safety_factor: float = 0.8) -> Tuple[bool, str, str]:
    """
    Check if there's enough memory available for processing.
    
    Args:
        estimated_memory: Estimated memory needed in bytes
        safety_factor: Use only this fraction of available memory (default: 0.8 = 80%)
        
    Returns:
        tuple: (is_safe, warning_level, message)
            - is_safe: True if memory is sufficient
            - warning_level: 'safe', 'warning', 'danger'
            - message: Human-readable message
    """
    available = get_available_memory()
    safe_available = available * safety_factor
    
    estimated_str = format_memory_size(estimated_memory)
    available_str = format_memory_size(available)
    
    if estimated_memory <= safe_available:
        return (True, 'safe', 
                f"Memory check passed. Estimated: {estimated_str}, Available: {available_str}")
    
    elif estimated_memory <= available:
        return (True, 'warning',
                f"WARNING: Memory warning: Estimated usage ({estimated_str}) is close to available memory ({available_str}). "
                f"Consider using batch processing or closing other applications.")
    
    else:
        return (False, 'danger',
                f"ERROR: Insufficient memory! Estimated: {estimated_str}, Available: {available_str}. "
                f"Processing may crash. Please use batch processing or reduce the number of videos.")


def calculate_optimal_batch_size(media_files: List[str], target_width: int = 1920,
                                 clip_duration: float = 5.0, safety_factor: float = 0.7) -> int:
    """
    Calculate optimal batch size based on available memory.
    
    Args:
        media_files: List of media file paths
        target_width: Target width for processing
        clip_duration: Average duration per clip
        safety_factor: Use only this fraction of available memory
        
    Returns:
        int: Recommended batch size (minimum 1)
    """
    if not media_files:
        return 1
    
    available = get_available_memory() * safety_factor
    
    # Estimate memory for a single file
    sample_file = media_files[0]
    ext = os.path.splitext(sample_file)[1].lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        single_file_memory = estimate_image_memory(sample_file, clip_duration, target_width)
    else:
        single_file_memory = estimate_video_memory(sample_file, target_width)
    
    # Account for assembly overhead
    single_file_memory = int(single_file_memory * 1.5)
    
    # Calculate how many files can fit
    batch_size = max(1, int(available / single_file_memory))
    
    # Cap at reasonable maximum (100 files per batch)
    batch_size = min(batch_size, 100)
    
    return batch_size
