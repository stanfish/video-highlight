import os
import argparse
import random
import gc
from src.utils.file_manager import get_media_files
from src.core.audio_processor import AudioProcessor
from src.core.video_processor import VideoProcessor
from src.utils.memory_monitor import (
    estimate_total_memory, 
    check_memory_safety, 
    calculate_optimal_batch_size,
    format_memory_size
)

def main():
    parser = argparse.ArgumentParser(description="AI Video Highlight Generator")
    parser.add_argument("--input", "-i", required=True, help="Input folder containing videos/photos")
    parser.add_argument("--audio", "-a", required=True, help="Background music file")
    parser.add_argument("--output", "-o", default="output.mp4", help="Output video file")
    parser.add_argument("--title", help="Title text to overlay on the video", default=None)
    parser.add_argument("--batch-size", type=int, default=0, 
                       help="Number of videos to process per batch (0 = auto-calculate)")
    parser.add_argument("--skip-memory-check", action="store_true",
                       help="Skip memory safety checks (use with caution)")
    parser.add_argument("--max-frames", type=int, default=100,
                       help="Maximum frames to analyze per video for AI scoring")
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
    
    transition_duration = 0.5
    num_media = len(all_media)
    
    # Calculate target duration per clip to fill the audio
    target_total_duration = audio_proc.duration + (num_media - 1) * transition_duration
    target_clip_duration = target_total_duration / num_media if num_media > 0 else 5.0
    
    print(f"Target Duration per clip: {target_clip_duration:.2f}s (Total Audio: {audio_proc.duration:.2f}s)")
    
    # 3. Memory Check
    if not args.skip_memory_check:
        print("\n=== Memory Safety Check ===")
        memory_estimate = estimate_total_memory(all_media, target_width=1920, clip_duration=target_clip_duration)
        
        print(f"Estimated memory needed: {format_memory_size(memory_estimate['total_estimated'])}")
        print(f"Estimated peak memory: {format_memory_size(memory_estimate['peak_memory'])}")
        
        is_safe, warning_level, message = check_memory_safety(memory_estimate['peak_memory'])
        print(message)
        
        if warning_level == 'danger':
            print("\nRECOMMENDATION: Use batch processing to prevent crashes.")
            if args.batch_size == 0:
                # Auto-calculate batch size
                batch_size = calculate_optimal_batch_size(all_media, target_width=1920, 
                                                         clip_duration=target_clip_duration)
                print(f"Auto-calculated batch size: {batch_size} videos per batch")
            else:
                batch_size = args.batch_size
        elif warning_level == 'warning':
            print("\nWARNING: Consider closing other applications to free up memory.")
            batch_size = args.batch_size if args.batch_size > 0 else num_media
        else:
            # Safe to process all at once
            batch_size = args.batch_size if args.batch_size > 0 else num_media
    else:
        print("Skipping memory check (--skip-memory-check enabled)")
        batch_size = args.batch_size if args.batch_size > 0 else num_media
    
    # 4. Process videos (with batching if needed)
    from src.core.ai_scorer import VideoScorer
    scorer = VideoScorer()
    
    video_proc = VideoProcessor()
    
    # Determine if we need batch processing
    use_batching = batch_size < num_media
    
    if use_batching:
        print(f"\n=== Batch Processing Mode ===")
        print(f"Processing {num_media} files in batches of {batch_size}")
        process_in_batches(all_media, args.audio, args.output, scorer, video_proc,
                          target_clip_duration, transition_duration, args.title, 
                          batch_size, args.max_frames)
    else:
        print(f"\n=== Standard Processing Mode ===")
        process_all_at_once(all_media, args.audio, args.output, scorer, video_proc,
                           target_clip_duration, transition_duration, args.title,
                           args.max_frames)
    
    print("\n=== Video generation complete! ===")


def process_all_at_once(all_media, audio_path, output_path, scorer, video_proc,
                        target_clip_duration, transition_duration, title_text, max_frames):
    """Process all media files at once (original behavior)."""
    selected_clips = []
    num_media = len(all_media)
    
    for i, media_path in enumerate(all_media):
        print(f"Processing {os.path.basename(media_path)}... ({i+1}/{num_media})")
        print(f"PROGRESS_UPDATE:{int(((i+1) / num_media) * 80)}")
        
        ext = os.path.splitext(media_path)[1].lower()
        is_image = ext in ['.jpg', '.jpeg', '.png']
        
        start_time = 0
        duration = target_clip_duration
        
        if not is_image:
             # Video: Find best segment of 'duration'
             scores = scorer.analyze_video(media_path, interval_sec=1.0, max_frames=max_frames)
             if scores:
                 # If video is shorter than target, use full video
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

    # Assemble
    video_proc.assemble_video(selected_clips, audio_path, output_path, 
                             transition_duration=transition_duration, 
                             output_width=1920, title_text=title_text)


def process_in_batches(all_media, audio_path, output_path, scorer, video_proc,
                      target_clip_duration, transition_duration, title_text, 
                      batch_size, max_frames):
    """Process media files in batches to limit memory usage."""
    import tempfile
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    
    num_media = len(all_media)
    num_batches = (num_media + batch_size - 1) // batch_size  # Ceiling division
    
    temp_dir = tempfile.mkdtemp(prefix="video_highlight_")
    batch_files = []
    
    try:
        # Process each batch
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, num_media)
            batch_media = all_media[start_idx:end_idx]
            
            print(f"\n--- Batch {batch_idx + 1}/{num_batches} ---")
            print(f"Processing files {start_idx + 1} to {end_idx} of {num_media}")
            
            selected_clips = []
            
            for i, media_path in enumerate(batch_media):
                global_idx = start_idx + i
                print(f"Processing {os.path.basename(media_path)}... ({global_idx+1}/{num_media})")
                print(f"PROGRESS_UPDATE:{int(((global_idx+1) / num_media) * 70)}")
                
                ext = os.path.splitext(media_path)[1].lower()
                is_image = ext in ['.jpg', '.jpeg', '.png']
                
                start_time = 0
                duration = target_clip_duration
                
                if not is_image:
                    scores = scorer.analyze_video(media_path, interval_sec=1.0, max_frames=max_frames)
                    if scores:
                        video_len = scores[-1][0] + 1.0
                        if video_len < duration:
                            duration = video_len
                            start_time = 0
                        else:
                            start_time, _ = find_best_window(scores, duration)
                
                clip = video_proc.create_clip(media_path, start_time=start_time, duration=duration)
                if clip:
                    selected_clips.append(clip)
            
            # Save this batch as a temporary video
            batch_output = os.path.join(temp_dir, f"batch_{batch_idx:03d}.mp4")
            print(f"Saving batch {batch_idx + 1} to temporary file...")
            
            # Create a temporary VideoProcessor for this batch
            batch_proc = VideoProcessor()
            # Don't add audio or title yet - just concatenate clips
            batch_proc.assemble_video(selected_clips, None, batch_output,
                                     transition_duration=transition_duration,
                                     output_width=1920, title_text=None)
            
            batch_files.append(batch_output)
            
            # Clean up clips from memory
            for clip in selected_clips:
                clip.close()
                del clip
            selected_clips.clear()
            gc.collect()
            
            print(f"Batch {batch_idx + 1} complete. Memory released.")
        
        # Now concatenate all batch files
        print(f"\n=== Final Assembly ===")
        print(f"Combining {len(batch_files)} batch files...")
        print(f"PROGRESS_UPDATE:80")
        
        final_clips = [VideoFileClip(bf) for bf in batch_files]
        final_video_proc = VideoProcessor()
        
        # Concatenate batches and add audio/title
        final_video_proc.assemble_video(final_clips, audio_path, output_path,
                                       transition_duration=0,  # Batches already have transitions
                                       output_width=1920, title_text=title_text)
        
        # Cleanup
        for clip in final_clips:
            clip.close()
        
    finally:
        # Clean up temporary files
        print("Cleaning up temporary files...")
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not remove temp directory: {e}")


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
