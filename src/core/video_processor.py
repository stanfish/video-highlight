from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, vfx, ImageClip, CompositeVideoClip
import random
from typing import List
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class VideoProcessor:
    def __init__(self):
        self.clips = []
        
    def create_clip(self, media_path: str, start_time: float, duration: float) -> VideoFileClip:
        """Creates a subclip from a video file or an image clip."""
        try:
            # Check extension
            ext = os.path.splitext(media_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                # It's an image
                clip = ImageClip(media_path, duration=duration)
                # Optional: Add a slow zoom or pan effect (Ken Burns) for polish?
                # For now, static image is fine.
                return clip
            else:
                # It's a video
                clip = VideoFileClip(media_path)
                # Ensure start_time is valid
                if start_time + duration > clip.duration:
                    start_time = max(0, clip.duration - duration)
                    
                subclip = clip.subclip(start_time, start_time + duration)
                return subclip
        except Exception as e:
            print(f"Error processing {media_path}: {e}")
            return None

    def create_title_clip(self, text: str, width: int, height: int, duration: float = 5.0) -> VideoFileClip:
        """Creates a transparent title clip using PIL."""
        # Create transparent image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load font (default to Arial or similar if available, else default)
        try:
            # Try to load a nice font
            font = ImageFont.truetype("arial.ttf", 80)
        except IOError:
            font = ImageFont.load_default()
            
        # Calculate text position (center)
        # Get text bounding box
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text with shadow for better visibility
        shadow_offset = 3
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        # Convert to numpy array for MoviePy
        img_np = np.array(img)
        
        # Create ImageClip
        txt_clip = ImageClip(img_np, duration=duration)
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
                # Ensure width is even
                new_width = target_width
                new_height = int(target_width / clip_ratio)
                if new_height % 2 != 0: new_height -= 1
                resized_content = clip.resize(width=new_width, height=new_height)
            else:
                # Clip is taller than target (fit to height)
                # Ensure height is even
                new_height = target_height
                new_width = int(target_height * clip_ratio)
                if new_width % 2 != 0: new_width -= 1
                resized_content = clip.resize(width=new_width, height=new_height)
            
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
        # Use settings compatible with Windows Media Player and most players
        final_video.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264',
            audio_codec='aac',
            preset='medium',  # Good balance of speed/quality
            ffmpeg_params=[
                '-profile:v', 'main',  # Use main profile for better compatibility
                '-level', '4.0',  # H.264 level 4.0 (supports 1080p)
                '-pix_fmt', 'yuv420p',  # Standard pixel format for compatibility
                '-crf', '23',  # Constant Rate Factor (18-28, lower = better quality)
            ]
        )
        print("Done!")
