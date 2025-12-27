from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, vfx, ImageClip, CompositeVideoClip
import random
from typing import List
import os
import subprocess
import json
from PIL import Image, ImageDraw, ImageFont, ExifTags
import numpy as np

class VideoProcessor:
    def __init__(self):
        self.clips = []

    def get_video_rotation(self, media_path: str) -> int:
        """
        Robustly detects video rotation using ffprobe, checking both tags and side_data.
        Returns the rotation in degrees (e.g. 90, -90, 180, 270) or 0 if none.
        """
        try:
            cmd = [
                "ffprobe", 
                "-v", "quiet", 
                "-print_format", "json", 
                "-show_streams", 
                media_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return 0
                
            data = json.loads(result.stdout)
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    # Check tags
                    tags = stream.get('tags', {})
                    if 'rotate' in tags:
                        return int(float(tags['rotate']))
                        
                    # Check side_data_list
                    side_data = stream.get('side_data_list', [])
                    for side in side_data:
                        if 'rotation' in side:
                            return int(float(side['rotation']))
            
            return 0
        except Exception as e:
            print(f"Error checking rotation for {media_path}: {e}")
            return 0
        
    def create_clip(self, media_path: str, start_time: float, duration: float) -> VideoFileClip:
        """Creates a subclip from a video file or an image clip."""
        try:
            # Check extension
            ext = os.path.splitext(media_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                # It's an image
                # Load with PIL to handle rotation
                pil_img = Image.open(media_path)
                
                # Handle EXIF Rotation
                try:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    
                    exif = pil_img._getexif()
                    if exif is not None:
                        exif = dict(exif.items())
                        orientation = exif.get(orientation)
                        
                        if orientation == 3:
                            pil_img = pil_img.rotate(180, expand=True)
                        elif orientation == 6:
                            pil_img = pil_img.rotate(270, expand=True)
                        elif orientation == 8:
                            pil_img = pil_img.rotate(90, expand=True)
                except (AttributeError, KeyError, IndexError):
                    # No EXIF or other error, ignore
                    pass
                
                # Convert back to numpy for MoviePy
                img_np = np.array(pil_img)
                clip = ImageClip(img_np, duration=duration)
                
                # Optional: Add a slow zoom or pan effect (Ken Burns) for polish?
                # For now, static image is fine.
                return clip
            else:
                # It's a video
                clip = VideoFileClip(media_path)
                
                # Aspect Ratio Correction based on Rotation Metadata
                # The user requested: "I do not want to change the rotation, I just want to fix it by adding black spacing"
                # This implies the video is visually stretched (fat) and needs to be squashed horizontally.
                rotation = self.get_video_rotation(media_path)
                if rotation in [90, -90, 270, -270]:
                    print(f"Detected vertical metadata ({rotation}). Applying squeeze correction instead of rotation.")
                    # Calculate new dimensions: Keep Height, Decrease Width
                    # Target Aspect Ratio: 9:16 approx (0.5625)
                    # Current Height likely 1080. New Width should be ~607.
                    new_width = int(clip.h * (9/16)) 
                    clip = clip.resize(newsize=(new_width, clip.h))

                # Ensure start_time is valid
                if start_time + duration > clip.duration:
                    start_time = max(0, clip.duration - duration)
                    
                subclip = clip.subclip(start_time, start_time + duration)
                return subclip
        except Exception as e:
            print(f"Error processing {media_path}: {e}")
            return None

    def create_title_clip(self, text: str, width: int, height: int, duration: float = 5.0) -> VideoFileClip:
        """Creates a cinematic title clip using PIL with animation."""
        # Create transparent image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load font - try to find a bold one
        font_size = 120
        try:
            # Try typical Windows fonts
            font = ImageFont.truetype("arialbd.ttf", font_size) # Arial Bold
        except IOError:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
            
        # Calculate text position (center)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text with thick outline (stroke)
        stroke_width = 6
        stroke_color = (0, 0, 0, 255) # Black
        text_color = (255, 215, 0, 255) # Gold
        
        # Draw outline
        for adj_x in range(-stroke_width, stroke_width + 1):
            for adj_y in range(-stroke_width, stroke_width + 1):
                draw.text((x + adj_x, y + adj_y), text, font=font, fill=stroke_color)
                
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Convert to numpy array for MoviePy
        img_np = np.array(img)
        
        # Create ImageClip
        txt_clip = ImageClip(img_np, duration=duration)
        
        # Add animations: Fade in and Fade out
        txt_clip = txt_clip.crossfadein(1.0).crossfadeout(1.0)
        
        return txt_clip

    def assemble_video(self, clips: List[VideoFileClip], audio_path: str, output_path: str, transition_duration: float = 0.5, output_width: int = 1920, title_text: str = None):
        """Concatenates clips and adds background music with transitions."""
        if not clips:
            print("No clips to assemble.")
            return

        print(f"Assembling {len(clips)} clips with {transition_duration}s crossfade...")
        
        # Apply crossfade to all clips except the first one
        # Also resize clips to target resolution
        processed_clips = []
        for i, clip in enumerate(clips):
            # Ensure dimensions are even (required by H.264 codec)
            target_width = output_width if output_width % 2 == 0 else output_width - 1
            target_height = int(output_width * 9 / 16)
            target_height = target_height if target_height % 2 == 0 else target_height - 1
            
            # Resize to fit within target dimensions while maintaining aspect ratio
            # Then center on black background (letterbox/pillarbox)
            
            # Calculate aspect ratios
            clip_ratio = clip.w / clip.h
            target_ratio = target_width / target_height
            
            if clip_ratio > target_ratio:
                # Clip is wider than target (fit to width)
                # Resize by width only to preserve aspect ratio
                resized_content = clip.resize(width=target_width)
            else:
                # Clip is taller than target (fit to height)
                # Resize by height only to preserve aspect ratio
                resized_content = clip.resize(height=target_height)
            
            # Composite onto black background
            # Note: CompositeVideoClip default background is transparent (black in mp4)
            final_clip = CompositeVideoClip([resized_content.set_position("center")], size=(target_width, target_height))
            
            if i > 0:
                final_clip = final_clip.crossfadein(transition_duration)
            processed_clips.append(final_clip)
            
        # Use negative padding to create overlap
        final_video = concatenate_videoclips(processed_clips, method="compose", padding=-transition_duration)
        
        # Add Title Overlay if requested
        if title_text:
            print(f"Adding title: {title_text}")
            title_clip = self.create_title_clip(title_text, final_video.w, final_video.h)
            # Overlay title on top of the video
            final_video = CompositeVideoClip([final_video, title_clip.set_position("center")])
        
        # Add audio and ensure video matches audio duration exactly
        if audio_path:
            print(f"Adding audio from {audio_path}...")
            audio = AudioFileClip(audio_path)
            
            # Ensure final video matches audio duration exactly
            if abs(final_video.duration - audio.duration) > 0.1:
                print(f"Adjusting video duration from {final_video.duration:.2f}s to match audio {audio.duration:.2f}s")
                # If video is shorter, slow it down slightly; if longer, speed it up
                speed_factor = final_video.duration / audio.duration
                final_video = final_video.fx(vfx.speedx, speed_factor)
                
            final_video = final_video.set_audio(audio)
            
        print(f"Writing output to {output_path}... (Resolution: {output_width}x{int(output_width * 9 / 16)})")
        
        # Configure encoding parameters (CPU - High Compatibility)
        print("Using CPU encoding (libx264)...")
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            ffmpeg_params=[
                '-profile:v', 'main',  # Use main profile for better compatibility
                '-level', '4.0',  # H.264 level 4.0 (supports 1080p)
                '-pix_fmt', 'yuv420p',  # Standard pixel format for compatibility
                '-crf', '23',  # Constant Rate Factor (18-28, lower = better quality)
            ],
            threads=os.cpu_count() or 4
        )
        print("Done!")
