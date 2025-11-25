import os
import argparse
import random
from src.utils.file_manager import get_media_files
from src.core.audio_processor import AudioProcessor
from src.core.video_processor import VideoProcessor

def main():
    parser = argparse.ArgumentParser(description="AI Video Highlight Generator")
    parser.add_argument("--input", "-i", required=True, help="Input folder containing videos/photos")
    parser.add_argument("--audio", "-a", required=True, help="Background music file")
    parser.add_argument("--output", "-o", default="output.mp4", help="Output video file")
    parser.add_argument("--title", help="Title text to overlay on the video", default=None)
    args = parser.parse_args()

    print(f"Input Directory: {args.input}")
    print(f"Audio File: {args.audio}")

    # 1. Scan files
    videos, images = get_media_files(args.input)
    print(f"Found {len(videos)} videos and {len(images)} images.")
    
    # Merge and sort by date (Modification time is usually more reliable for "Date Taken" on copied files)
    all_media = videos + images
    all_media.sort(key=lambda x: os.path.getmtime(x))
    
    if not all_media:
        print("No media found. Exiting.")
        return

    # 2. Analyze Audio (for duration only)
    audio_proc = AudioProcessor(args.audio)
    audio_proc.load_audio()
    # beats = audio_proc.detect_beats() # Not using beats for now to ensure even distribution
    
    # 3. Generate Clips
    from src.core.ai_scorer import VideoScorer
    scorer = VideoScorer()
    
    video_proc = VideoProcessor()
    selected_clips = []
    
    transition_duration = 0.5
    num_media = len(all_media)
    
    # Calculate target duration per clip to fill the audio
    # Total video length = Sum(clips) - (N-1)*transition
    # We want Total video length = Audio Duration
    # Sum(clips) = Audio Duration + (N-1)*transition
    target_total_duration = audio_proc.duration + (num_media - 1) * transition_duration
    target_clip_duration = target_total_duration / num_media if num_media > 0 else 5.0
    
    print(f"Target Duration per clip: {target_clip_duration:.2f}s (Total Audio: {audio_proc.duration:.2f}s)")
    
    for i, media_path in enumerate(all_media):
        print(f"Processing {os.path.basename(media_path)}... ({i+1}/{num_media})")
        print(f"PROGRESS_UPDATE:{int(((i+1) / num_media) * 80)}")
        
        ext = os.path.splitext(media_path)[1].lower()
        is_image = ext in ['.jpg', '.jpeg', '.png']
        
        start_time = 0
        duration = target_clip_duration
        
        if not is_image:
             # Video: Find best segment of 'duration'
             scores = scorer.analyze_video(media_path, interval_sec=1.0)
             if scores:
                 # If video is shorter than target, use full video
                 # Scorer returns list of (time, score). Last time is approx duration.
                 video_len = scores[-1][0] + 1.0 # approx
                 
                 if video_len < duration:
                     duration = video_len
                     start_time = 0
                 else:
                     # Find best window
                     start_time, _ = find_best_window(scores, duration)
             else:
                 # Fallback if scorer fails
                 pass
        
        clip = video_proc.create_clip(media_path, start_time=start_time, duration=duration)
        if clip:
            selected_clips.append(clip)

    # 4. Assemble
    video_proc.assemble_video(selected_clips, args.audio, args.output, transition_duration=transition_duration, output_width=1920, title_text=args.title)

def find_best_window(scores, duration):
    best_start = 0
    best_score = -1
    
    for i in range(len(scores)):
        t, s = scores[i]
        if t + duration > scores[-1][0]:
            break
        
        # Calculate avg score for this window
        # Simple approximation: just take the score at start? 
        # Better: Average of all scores within [t, t+duration]
        window_scores = [sc for time, sc in scores if t <= time <= t + duration]
        if not window_scores:
            continue
        avg_score = sum(window_scores) / len(window_scores)
        
        if avg_score > best_score:
            best_score = avg_score
            best_start = t
            
    return best_start, best_score

def get_window_score(scores, start_time, duration):
    window_scores = [sc for time, sc in scores if start_time <= time <= start_time + duration]
    if not window_scores:
        return 0.0
    return sum(window_scores) / len(window_scores)

if __name__ == "__main__":
    main()
