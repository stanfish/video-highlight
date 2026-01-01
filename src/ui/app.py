import streamlit as st
import os
import glob
from pathlib import Path
import sys

# Add project root to path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import memory monitoring utilities
from src.utils.memory_monitor import (
    estimate_total_memory,
    check_memory_safety,
    calculate_optimal_batch_size,
    format_memory_size
)
from src.utils.file_manager import get_media_files

st.set_page_config(page_title="AI Video Highlight Generator", page_icon="🎬", layout="wide")

st.title("🎬 AI Video Highlight Generator")
st.markdown("Turn your raw footage into a cinematic highlight reel automatically.")

# --- Sidebar / Configuration ---
st.sidebar.header("Configuration")

# 1. Input Folder
st.sidebar.subheader("1. Media Source")

# Use session state to track and clean the input
if 'input_folder_raw' not in st.session_state:
    st.session_state.input_folder_raw = ""

input_folder_raw = st.sidebar.text_input("Input Folder Path", 
                                          value=st.session_state.input_folder_raw,
                                          placeholder=r"C:\path\to\your\videos")

# Auto-clean quotes from the input
input_folder = input_folder_raw.strip().strip('"').strip("'")

# Update session state with cleaned value for next render
if input_folder != st.session_state.input_folder_raw:
    st.session_state.input_folder_raw = input_folder
    st.rerun()

# 2. Music Selection
st.sidebar.subheader("2. Background Music")
music_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bg_music")
os.makedirs(music_folder, exist_ok=True)

music_files = glob.glob(os.path.join(music_folder, "*.mp3"))

# Get duration for each music file and create formatted options
from moviepy.editor import AudioFileClip

def get_audio_duration(file_path):
    """Get duration of audio file in seconds"""
    try:
        audio = AudioFileClip(file_path)
        duration = audio.duration
        audio.close()
        return duration
    except:
        return 0

def format_duration(seconds):
    """Format seconds as MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

# Create list of (display_name, file_path, duration) tuples
music_data = []
for f in music_files:
    duration = get_audio_duration(f)
    basename = os.path.basename(f)
    display_name = f"{format_duration(duration)} - {basename}"
    music_data.append((display_name, f, duration))

# Sort by duration (longest first)
music_data.sort(key=lambda x: x[2], reverse=True)

# Create options dict with display names
music_options = {item[0]: item[1] for item in music_data}

selected_music_name = st.sidebar.selectbox(
    "Select Music Track", 
    options=list(music_options.keys()) if music_files else ["No music found"],
    index=0 if music_files else 0
)

if not music_files:
    st.sidebar.warning(f"No .mp3 files found in {music_folder}. Please add some music!")
    selected_music_path = None
else:
    selected_music_path = music_options[selected_music_name]
    st.sidebar.audio(selected_music_path)

# 3. Title Overlay
st.sidebar.subheader("3. Video Title (Optional)")
video_title = st.sidebar.text_input("Title Text", placeholder="My Awesome Trip 2025")

# 4. Output Settings
st.sidebar.subheader("4. Output")
# Auto-generate filename from video title
if video_title:
    # Replace spaces with underscores and sanitize
    sanitized_title = video_title.replace(" ", "_").replace("-", "_")
    default_filename = f"highlight_{sanitized_title}.mp4"
else:
    default_filename = "highlight_video.mp4"
    
output_filename = st.sidebar.text_input("Output Filename", value=default_filename)

# 5. Advanced Settings
st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ Advanced Settings"):
    st.markdown("**Memory Management**")
    batch_size = st.number_input(
        "Batch Size (0 = auto)",
        min_value=0,
        max_value=100,
        value=0,
        help="Process videos in batches to limit memory usage. 0 = auto-calculate based on available memory."
    )
    
    max_frames = st.number_input(
        "Max Frames per Video",
        min_value=10,
        max_value=500,
        value=100,
        help="Maximum frames to analyze per video for AI scoring. Lower values use less memory."
    )
    
    skip_memory_check = st.checkbox(
        "Skip memory check",
        value=False,
        help="Skip memory safety checks (not recommended)"
    )

st.sidebar.markdown("---")
# Scroll to Bottom Button using CSS/JS Injection
# We use a Streamlit component to run Javascript, and custom CSS to position the iframe.
import streamlit.components.v1 as components

# HTML/JS for the button
# Robust Scroll to Bottom Button (Injects into parent DOM)
import streamlit.components.v1 as components

# JavaScript to create a fixed button in the main window (breaking out of iframe)
js_code = """
<script>
    (function() {
        // ID to prevent duplicate buttons
        var btnId = "floating-scroll-btn-fixed";
        
        // Remove existing button if present (cleanup)
        var existing = window.parent.document.getElementById(btnId);
        if (existing) {
            existing.remove();
        }
        
        // Create Button
        var btn = window.parent.document.createElement("button");
        btn.id = btnId;
        btn.innerText = "⬇️ Scroll to Bottom";
        
        // Style Button
        btn.style.position = "fixed";
        btn.style.bottom = "20px";
        btn.style.right = "20px";
        btn.style.zIndex = "999999";
        btn.style.backgroundColor = "#FF4B4B";
        btn.style.color = "white";
        btn.style.border = "none";
        btn.style.borderRadius = "50px";
        btn.style.padding = "10px 20px";
        btn.style.fontWeight = "bold";
        btn.style.cursor = "pointer";
        btn.style.boxShadow = "0px 4px 6px rgba(0,0,0,0.1)";
        btn.style.transition = "background-color 0.3s";
        
        // Hover effect
        btn.onmouseover = function() {
            btn.style.backgroundColor = "#FF2B2B";
        };
        btn.onmouseout = function() {
            btn.style.backgroundColor = "#FF4B4B";
        };
        
        // Click Action
        btn.onclick = function() {
            // Priority 1: The active target during generation (inside the loop)
            var target = window.parent.document.getElementById('active-scroll-target');
            
            // Priority 2: The static target at the bottom of the page (idle state)
            if (!target) {
                target = window.parent.document.getElementById('bottom-of-page');
            }
            
            if (target) {
                target.scrollIntoView({behavior: 'smooth', block: 'end'});
            } else {
                // Fallback: Aggressive scroll if anchors missing
                var scrollTargets = [
                    window.parent.document.querySelector('[data-testid="stAppViewContainer"]'),
                    window.parent.document.querySelector('section.main')
                ];
                scrollTargets.forEach(function(el) {
                    if (el) try { el.scrollTo({top: el.scrollHeight, behavior: 'smooth'}); } catch(e){}
                });
            }
        };
        
        // Append to Parent Body
        window.parent.document.body.appendChild(btn);
    })();
</script>
"""

# Inject the script
components.html(js_code, height=0, width=0)


# --- Main Area ---

if st.sidebar.button("Generate Highlight Video", type="primary"):
    if not input_folder or not os.path.exists(input_folder):
        st.error("Please enter a valid input folder path.")
    elif not selected_music_path:
        st.error("Please select a background music track.")
    else:
        # Memory check before processing
        if not skip_memory_check:
            st.info("🔍 Checking memory requirements...")
            
            try:
                # Get media files
                videos, images = get_media_files(input_folder)
                all_media = videos + images
                
                if not all_media:
                    st.error("No media files found in the input folder.")
                    st.stop()
                
                st.write(f"Found {len(videos)} videos and {len(images)} images.")
                
                # Estimate memory
                from moviepy.editor import AudioFileClip
                audio = AudioFileClip(selected_music_path)
                audio_duration = audio.duration
                audio.close()
                
                num_media = len(all_media)
                transition_duration = 0.5
                target_total_duration = audio_duration + (num_media - 1) * transition_duration
                target_clip_duration = target_total_duration / num_media if num_media > 0 else 5.0
                
                memory_estimate = estimate_total_memory(all_media, target_width=1920, 
                                                        clip_duration=target_clip_duration)
                
                # Display memory info
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Estimated Memory", format_memory_size(memory_estimate['total_estimated']))
                with col2:
                    st.metric("Peak Memory", format_memory_size(memory_estimate['peak_memory']))
                
                # Check safety
                is_safe, warning_level, message = check_memory_safety(memory_estimate['peak_memory'])
                
                if warning_level == 'danger':
                    st.error(message)
                    recommended_batch = calculate_optimal_batch_size(all_media, target_width=1920,
                                                                    clip_duration=target_clip_duration)
                    st.warning(f"⚠️ **Recommendation**: Enable batch processing with batch size {recommended_batch} to prevent crashes.")
                    st.info("You can configure batch size in Advanced Settings above.")
                    
                    if batch_size == 0:
                        st.error("❌ Cannot proceed without batch processing. Please set a batch size in Advanced Settings.")
                        st.stop()
                elif warning_level == 'warning':
                    st.warning(message)
                    st.info("💡 Consider closing other applications or enabling batch processing.")
                else:
                    st.success(message)
                    
            except Exception as e:
                st.warning(f"Could not estimate memory requirements: {e}")
                st.info("Proceeding anyway...")
        # Create a placeholder for logs/progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.info("Starting generation process... This may take a few minutes.")
            
            # Calculate project root securely
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            
            # Define output path
            output_path = os.path.join(project_root, output_filename)
            
            # Clean inputs
            clean_input_folder = input_folder.strip().strip('"').strip("'")
            
            # Call the main processing function
            with st.spinner("Analyzing media, scoring clips, and rendering video..."):
                import subprocess
                
                # Construct command
                cmd = [
                    sys.executable, "-m", "src.main",
                    "--input", clean_input_folder,
                    "--audio", selected_music_path,
                    "--output", output_path
                ]
                
                if video_title:
                    cmd.extend(["--title", video_title])
                
                # Add batch size and max frames
                if batch_size > 0:
                    cmd.extend(["--batch-size", str(batch_size)])
                
                cmd.extend(["--max-frames", str(max_frames)])
                
                if skip_memory_check:
                    cmd.append("--skip-memory-check")
                
                # Run as subprocess
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    cwd=project_root
                )
                
                # Stream output to UI
                log_container = st.expander("Process Logs", expanded=True)
                
                # Render a scroll target HERE so it exists while the loop below is running
                st.markdown("<div id='active-scroll-target'></div>", unsafe_allow_html=True)
                
                with log_container:
                    # Use iter(process.stdout.readline, '') to read line by line
                    for line in iter(process.stdout.readline, ''):
                        line = line.strip()
                        if not line: continue
                        
                        st.text(line)
                        
                        # Parse progress
                        if "PROGRESS_UPDATE:" in line:
                            try:
                                pct = int(line.split(":")[-1])
                                progress_bar.progress(pct)
                                status_text.text(f"Processing media... {pct}%")
                            except:
                                pass
                        
                        # Parse MoviePy progress (rendering)
                        # MoviePy output format: "t:  41%|..."
                        if "t:" in line and "%" in line:
                            try:
                                # Extract percentage
                                import re
                                match = re.search(r"(\d+)%", line)
                                if match:
                                    render_pct = int(match.group(1))
                                    # Map 0-100 rendering to 80-100 overall
                                    overall_pct = 80 + int(render_pct * 0.2)
                                    progress_bar.progress(overall_pct)
                                    status_text.text(f"Rendering video... {render_pct}%")
                            except:
                                pass
                
                process.wait()
                
                if process.returncode == 0:
                    st.success("Video generated successfully!")
                    st.video(output_path)
                    st.balloons()
                else:
                    st.error("An error occurred during generation. Check logs above.")
                    
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

st.markdown("---")
st.markdown("### Instructions")
st.markdown("""
1.  **Paste the folder path** containing your videos and photos.
2.  **Select a music track** from the dropdown (add .mp3 files to the `bg_music` folder in the project root).
3.  (Optional) **Enter a title** for your video.
4.  Click **Generate Highlight Video**.
""")

# Anchor for robust scrolling
st.markdown("<div id='bottom-of-page'></div>", unsafe_allow_html=True)


