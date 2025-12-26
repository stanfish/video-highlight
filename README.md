# AI Video Highlight Generator 🎬

A local Windows application that automatically generates cinematic highlight videos from your raw footage and photos. It uses AI (CLIP) to identify the best moments, synchronizes cuts to the beat of your music, and applies smooth transitions.

## Features

*   **AI-Powered Selection**: Uses OpenAI's CLIP model to score frames and select the most aesthetically pleasing and relevant moments from your videos.
*   **Smart Duration Matching**: Automatically calculates clip durations to ensure your video ends exactly when the music ends. It distributes clips evenly to avoid rushing or dragging.
*   **Mixed Media Support**: Seamlessly handles both videos (`.mp4`, `.mov`) and photos (`.jpg`, `.png`).
*   **Smart Resizing**:
    *   Outputs in **Full HD (1920x1080)**.
    *   Automatically applies **letterboxing/pillarboxing** to preserve the original aspect ratio of photos and videos (no cropping or stretching).
*   **Title Overlay**: Add a custom, animated title to the beginning of your video.
*   **Local Processing**: Runs entirely on your machine. No data is uploaded to the cloud.

## Prerequisites

*   **OS**: Windows 10/11
*   **Hardware**: NVIDIA GPU recommended (for faster AI scoring), but works on CPU.
*   **Software**:
    *   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
    *   **FFmpeg**: Essential for video processing.
        1.  Download the "full" build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
        2.  Extract the folder (e.g., to `C:\ffmpeg`).
        3.  Add `C:\ffmpeg\bin` to your System Environment Variables -> Path.
        4.  Verify by running `ffmpeg -version` in a new terminal.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/video-highlight.git
    cd video-highlight
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

    > **Note for NVIDIA GPU Users**: To enable GPU acceleration for faster AI scoring, you should install the CUDA version of PyTorch. Run this command *after* the above:
    > ```bash
    > pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
    > ```
    > (Check [pytorch.org](https://pytorch.org/get-started/locally/) for the command matching your CUDA version).

## Usage

### Option 1: User Interface (Recommended)

This is the easiest way to use the tool.

1.  **Run the App**:
    Open your terminal in the project folder and run:
    ```bash
    python -m streamlit run src/ui/app.py
    ```
    This will open the interface in your web browser.

2.  **Configure**:
    *   **Media Source**: Paste the full path to the folder containing your photos and videos (e.g., `C:\Users\You\Videos\Trip`).
    *   **Background Music**: Select a track from the dropdown.
        *   *Tip*: Add your own `.mp3` files to the `bg_music` folder in the project directory to see them here.
    *   **Video Title**: (Optional) Enter a title to overlay on the video.
    *   **Output Filename**: Name your result file.

3.  **Generate**:
    Click **Generate Highlight Video**. The progress bar will show the status of analyzing, scoring, and rendering.

### Option 2: Command Line Interface (CLI)

For advanced users or automation.

```bash
python -m src.main --input "C:\path\to\media" --audio "C:\path\to\music.mp3" --output "my_video.mp4" --title "My Trip"
```

**Arguments:**
*   `--input`, `-i`: Path to folder containing media.
*   `--audio`, `-a`: Path to background music file.
*   `--output`, `-o`: Output video filename (default: `output.mp4`).
*   `--title`: Text to overlay at the start.

## Troubleshooting

*   **"MoviePy error: FFMPEG..."**: This means FFmpeg is not found. Double-check that the `bin` folder inside your FFmpeg installation is added to your system PATH environment variable. Restart your terminal after changing environment variables.
*   **Slow Processing**: AI scoring is computationally intensive.
    *   If you have an NVIDIA GPU, ensure you installed the CUDA version of PyTorch (see Installation).
    *   On CPU, this process will take significantly longer.
*   **"No media found"**: Ensure your input path is correct and contains `.mp4`, `.mov`, `.jpg`, or `.png` files.

## License

MIT
