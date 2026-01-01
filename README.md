# AI Video Highlight Generator 🎬

A powerful Windows application that automatically generates cinematic highlight videos from your raw footage and photos. It uses AI (CLIP) to identify the best moments, synchronizes cuts to your music, and applies smooth transitions—all while intelligently managing memory to handle large video collections without crashes.

## ✨ Features

### Core Capabilities
*   **AI-Powered Selection**: Uses OpenAI's CLIP model to score frames and select the most aesthetically pleasing moments from your videos
*   **Smart Duration Matching**: Automatically calculates clip durations to match your music length perfectly
*   **Mixed Media Support**: Seamlessly handles both videos (`.mp4`, `.mov`) and photos (`.jpg`, `.png`)
*   **Smart Resizing**: Outputs in Full HD (1920x1080) with automatic letterboxing/pillarboxing to preserve aspect ratios
*   **Title Overlay**: Add custom, animated titles to your videos
*   **Local Processing**: Runs entirely on your machine—no cloud uploads required

### Memory Optimization (New!)
*   **Intelligent Memory Management**: Automatically estimates memory requirements before processing
*   **Batch Processing**: Handles 100+ videos without crashes by processing in manageable groups
*   **Proactive Warnings**: Alerts you if memory is insufficient and recommends optimal settings
*   **Auto-Configuration**: Calculates ideal batch sizes based on your available system memory

## 📋 Prerequisites

*   **OS**: Windows 10/11
*   **RAM**: 8 GB minimum, 16 GB+ recommended for large video collections
*   **Disk Space**: ~15-20 GB free space for processing temporary files
*   **Hardware**: NVIDIA GPU recommended for faster AI scoring (works on CPU too)
*   **Software**:
    *   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
    *   **FFmpeg**: Essential for video processing
        1.  Download the "full" build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
        2.  Extract to a folder (e.g., `C:\ffmpeg`)
        3.  Add `C:\ffmpeg\bin` to your System PATH environment variable
        4.  Verify installation: `ffmpeg -version` in terminal

## 🚀 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/video-highlight.git
    cd video-highlight
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

    > **Note for NVIDIA GPU Users**: For GPU acceleration, install CUDA-enabled PyTorch:
    > ```bash
    > pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
    > ```
    > Check [pytorch.org](https://pytorch.org/get-started/locally/) for your CUDA version.

3.  **Download AI model (optional but recommended)**:
    ```bash
    python download_models.py
    ```
    This downloads the CLIP model (~600MB) for offline use.

## 💡 Usage

### Option 1: User Interface (Recommended)

The easiest way to create highlight videos with full memory management.

1.  **Launch the app**:
    ```bash
    python -m streamlit run src/ui/app.py
    ```
    Opens in your web browser automatically.

2.  **Configure your video**:
    *   **Media Source**: Paste the folder path containing your videos/photos
        *   Example: `C:\Users\You\Videos\Trip`
    *   **Background Music**: Select from dropdown
        *   Add your own `.mp3` files to the `bg_music` folder
    *   **Video Title**: (Optional) Add a custom title overlay
    *   **Output Filename**: Name your final video

3.  **Advanced Settings** (for large video collections):
    *   Click "⚙️ Advanced Settings" in the sidebar
    *   **Batch Size**: Set to 0 for auto-calculation, or specify manually
    *   **Max Frames**: Limit AI analysis frames to reduce memory (default: 100)
    *   **Skip Memory Check**: Bypass safety warnings (not recommended)

4.  **Generate**:
    *   Click **Generate Highlight Video**
    *   Review memory estimate and warnings
    *   If memory is insufficient, the app will recommend batch processing
    *   Monitor progress in real-time

### Option 2: Command Line Interface

For automation or advanced users.

**Basic usage**:
```bash
python -m src.main --input "C:\path\to\media" --audio "bg_music\song.mp3" --output "my_video.mp4"
```

**With title**:
```bash
python -m src.main --input "C:\path\to\media" --audio "bg_music\song.mp3" --output "my_video.mp4" --title "Summer 2025"
```

**With batch processing** (for large collections):
```bash
python -m src.main --input "C:\path\to\media" --audio "bg_music\song.mp3" --output "my_video.mp4" --batch-size 10
```

**All available arguments**:
*   `--input`, `-i`: Path to folder containing media (required)
*   `--audio`, `-a`: Path to background music file (required)
*   `--output`, `-o`: Output video filename (default: `output.mp4`)
*   `--title`: Text overlay for the video
*   `--batch-size`: Videos per batch (0 = auto-calculate, default: 0)
*   `--max-frames`: Max frames to analyze per video (default: 100)
*   `--skip-memory-check`: Skip memory safety checks (use with caution)

## 🧠 Memory Management

### How It Works

The app automatically:
1. **Estimates** memory needed for your videos
2. **Compares** with available system memory
3. **Warns** you if processing might crash
4. **Recommends** optimal batch size
5. **Processes** videos in groups if needed

### When to Use Batch Processing

| Video Count | Typical Behavior | Recommendation |
|-------------|------------------|----------------|
| 1-20 videos | Processes all at once | No batch needed |
| 20-50 videos | May show warning | Optional batching |
| 50+ videos | Shows error without batching | **Batch required** |

### Memory Warnings Explained

*   **✅ Green (Safe)**: Sufficient memory, proceed normally
*   **⚠️ Yellow (Warning)**: Close to limits, consider batching
*   **❌ Red (Danger)**: Insufficient memory, batching required

### Batch Processing Details

**What happens**:
1. Videos split into groups (e.g., 10 per batch)
2. Each batch processed independently
3. Temporary files saved to system temp folder
4. Memory released between batches
5. All batches combined into final video
6. Temporary files automatically deleted

**Temporary files location**: `C:\Users\<You>\AppData\Local\Temp\video_highlight_*`

**Disk space needed**: ~2-3 GB per batch (automatically cleaned up)

## 🎯 Examples

### Small Collection (10 videos)
```bash
python -m src.main -i "C:\Videos\Vacation" -a "bg_music\song.mp3" -o "vacation.mp4"
```
→ Processes all at once, ~2-3 minutes

### Large Collection (50+ videos)
```bash
python -m src.main -i "C:\Videos\YearInReview" -a "bg_music\song.mp3" -o "year2025.mp4" --batch-size 15
```
→ Processes in batches, ~10-15 minutes, prevents crashes

### With Custom Settings
```bash
python -m src.main -i "C:\Videos\Trip" -a "bg_music\song.mp3" -o "trip.mp4" --title "Europe 2025" --max-frames 50 --batch-size 10
```
→ Lower memory usage, custom title, batch processing

## 🔧 Troubleshooting

### Memory Issues
*   **"Insufficient memory" error**: 
    *   Enable batch processing (set `--batch-size 10` or use UI Advanced Settings)
    *   Close other applications to free up RAM
    *   Reduce `--max-frames` to lower memory usage
*   **Process crashes mid-generation**:
    *   Reduce batch size (try `--batch-size 5`)
    *   Ensure you have 15+ GB free disk space

### FFmpeg Issues
*   **"MoviePy error: FFMPEG not found"**: 
    *   Verify FFmpeg is in your PATH: `ffmpeg -version`
    *   Restart terminal after adding to PATH
    *   Reinstall FFmpeg if needed

### Performance Issues
*   **Slow AI scoring**:
    *   Install CUDA-enabled PyTorch for GPU acceleration
    *   Reduce `--max-frames` (e.g., `--max-frames 50`)
    *   On CPU, processing is naturally slower
*   **Batch processing is slow**:
    *   Increase batch size if you have more RAM
    *   Use SSD instead of HDD for faster temp file I/O

### Other Issues
*   **"No media found"**: 
    *   Check folder path is correct
    *   Ensure files are `.mp4`, `.mov`, `.jpg`, or `.png`
*   **Unicode errors in console**: 
    *   This is a Windows console limitation, doesn't affect processing
    *   Use the UI instead for better experience

## 📊 Performance Guide

| System Specs | Max Videos (No Batch) | Recommended Batch Size |
|--------------|----------------------|------------------------|
| 8 GB RAM | ~15-20 videos | 5-8 videos/batch |
| 16 GB RAM | ~30-40 videos | 10-15 videos/batch |
| 32 GB RAM | ~60-80 videos | 20-30 videos/batch |
| 64 GB RAM | 100+ videos | No batch needed |

*Note: Actual limits vary based on video resolution and duration*

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

*   OpenAI CLIP model for AI-powered frame scoring
*   MoviePy for video processing
*   Streamlit for the user interface
*   FFmpeg for video encoding/decoding

---

**Made with ❤️ for creating beautiful video memories**
