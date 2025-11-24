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

    # 2. Analyze Audio
    audio_proc = AudioProcessor(args.audio)
    audio_proc.load_audio()
    beats = audio_proc.detect_beats()
    
    # 3. Generate Clips (AI Powered)
    from src.core.ai_scorer import VideoScorer
    scorer = VideoScorer()
    
    video_proc = VideoProcessor()
    selected_clips = []
    
    # Calculate pacing strategy
    # If we have many files and short audio, we must limit clip duration to fit more files.
    total_audio_duration = audio_proc.duration
    num_media = len(all_media)
    avg_time_per_media = total_audio_duration / num_media if num_media > 0 else 5.0
    
    # Estimate beat duration
    avg_beat_duration = (beats[-1] - beats[0]) / len(beats) if len(beats) > 1 else 0.5
    
    # Calculate target beats per clip
    target_beats = int(avg_time_per_media / avg_beat_duration)
    
    # Snap to 4, 8, 12, 16
    if target_beats >= 14: max_beats_allowed = 16
    elif target_beats >= 10: max_beats_allowed = 12
    elif target_beats >= 6: max_beats_allowed = 8
    else: max_beats_allowed = 4
    
    print(f"Pacing Strategy: Avg {avg_time_per_media:.1f}s/file -> Max {max_beats_allowed} beats/clip")

    current_beat_idx = 0
    media_idx = 0
    
    while current_beat_idx < len(beats):
        # Loop media if we run out to ensure video matches audio length
        if media_idx >= len(all_media):
            print("All media used once. Looping back to start.")
            media_idx = 0
            
        media_path = all_media[media_idx]
        media_idx += 1 # Move to next media for next iteration
        
        # Determine max possible duration for this clip based on remaining audio
        remaining_audio_duration = audio_proc.duration - beats[current_beat_idx]
        if remaining_audio_duration < 2.0: # Too short
            break
            
        print(f"Processing {os.path.basename(media_path)}... ({media_idx}/{len(all_media)})")
        print(f"PROGRESS_UPDATE:{int((media_idx / len(all_media)) * 80)}") # Analysis is 0-80%
        
        # Check if it's an image or video
        ext = os.path.splitext(media_path)[1].lower()
        is_image = ext in ['.jpg', '.jpeg', '.png']
        
        best_start = 0
        final_duration = 0
        final_beats = 4 # Default to 4 beats
        
        if is_image:
            # For images, we just show them for 4 beats (or 8 if we want slow pace)
            start_time_audio = beats[current_beat_idx]
            if current_beat_idx + 4 < len(beats):
                end_time_audio = beats[current_beat_idx + 4]
                final_duration = end_time_audio - start_time_audio
                final_beats = 4
            else:
                final_duration = remaining_audio_duration
                final_beats = len(beats) - current_beat_idx
                
            print(f"Image clip duration: {final_duration:.1f}s")
            
        else:
            # Video analysis logic
            scores = scorer.analyze_video(media_path, interval_sec=1.0)
            if not scores:
                print("No scores found, skipping.")
                continue
                
            # Find best segment - try progressively longer durations
            base_beats = 4
            if current_beat_idx + base_beats >= len(beats):
                # Use remaining beats
                remaining_beats = len(beats) - current_beat_idx
                if remaining_beats > 0:
                    start_time_audio = beats[current_beat_idx]
                    # Use the time until the last beat as the duration
                    end_time_audio = beats[-1] + (beats[-1] - beats[-2]) if len(beats) > 1 else beats[-1] + 2.0
                    final_duration = end_time_audio - start_time_audio
                    best_start, _ = find_best_window(scores, final_duration)
                    final_beats = remaining_beats
                    print(f"Final clip: {best_start:.1f}s (Duration: {final_duration:.1f}s)")
                else:
                    break
            else:
                start_time_audio = beats[current_beat_idx]
                end_time_audio_4 = beats[current_beat_idx + base_beats]
                duration_4 = end_time_audio_4 - start_time_audio
                
                # Find best 4-beat window in video
                best_start, best_score_4 = find_best_window(scores, duration_4)
                
                final_duration = duration_4
                final_beats = base_beats
                
                # Try progressively longer clips: 8, 12, 16 beats (up to max_beats_allowed)
                for multiplier in [2, 3, 4]:
                    if base_beats * multiplier > max_beats_allowed:
                        break
                        
                    if current_beat_idx + base_beats * multiplier < len(beats):
                        end_time_audio_n = beats[current_beat_idx + base_beats * multiplier]
                        duration_n = end_time_audio_n - start_time_audio
                        
                        score_n = get_window_score(scores, best_start, duration_n)
                        
                        # Accept longer clip if score is >= 85% of base score
                        if score_n > best_score_4 * 0.85:
                            print(f"Extending clip to {base_beats * multiplier} beats ({duration_n:.1f}s) - Score: {score_n:.2f} vs {best_score_4:.2f}")
                            final_duration = duration_n
                            final_beats = base_beats * multiplier
                
                print(f"Selected start: {best_start:.1f}s (Duration: {final_duration:.1f}s)")
        
        clip = video_proc.create_clip(media_path, start_time=best_start, duration=final_duration)
        
        if clip:
            selected_clips.append(clip)
            
        current_beat_idx += final_beats


    # 4. Assemble
    video_proc.assemble_video(selected_clips, args.audio, args.output, transition_duration=0.5, output_width=1920, title_text=args.title)

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
