# AI Video Highlight Generator 🎬

A local Windows application that automatically generates cinematic highlight videos from your raw footage and photos. It uses AI (CLIP) to identify the best moments, synchronizes cuts to the beat of your music, and applies smooth transitions.

## Features

*   **AI-Powered Selection**: Uses OpenAI's CLIP model to score frames and select the most aesthetically pleasing and relevant moments.
*   **Beat Synchronization**: Automatically detects beats in your background music and cuts video clips to match the rhythm.
*   **Smart Duration**: Prioritizes longer, continuous clips (up to ~11s) to avoid rapid-fire repetition and provide a more cinematic feel.
*   **Mixed Media**: Handles both videos (`.mp4`, `.mov`) and photos (`.jpg`, `.png`).
*   **Smart Resizing**:
    *   Outputs in **Full HD (1920x1080)**.
    *   Automatically applies **letterboxing/pillarboxing** to preserve the original aspect ratio of photos and videos (no cropping or stretching).
*   **Title Overlay**: Add a custom title to the beginning of your video.
*   **Local Processing**: Runs entirely on your machine. No data is uploaded to the cloud.

## Prerequisites

*   **OS**: Windows 10/11
*   **Hardware**: NVIDIA GPU recommended (for faster AI scoring), but works on CPU.
*   **Software**:
    *   Python 3.10+
    *   [FFmpeg](https://ffmpeg.org/download.html) (Installed and added to system PATH)

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

## Usage

### Option 1: User Interface (Recommended)

1.  Run the Streamlit app:
    ```bash
    python -m streamlit run src/ui/app.py
    ```
2.  **Media Source**: Paste the full path to the folder containing your photos and videos.
3.  **Background Music**: Select a track from the dropdown.
    *   *Note*: Add your own `.mp3` files to the `bg_music` folder in the project directory.
4.  **Title**: (Optional) Enter a title for your video.
5.  Click **Generate Highlight Video**.

### Option 2: Command Line Interface (CLI)

You can also run the generator directly from the terminal:

```bash
python -m src.main --input "C:\path\to\media" --audio "C:\path\to\music.mp3" --output "my_highlight.mp4" --title "My Trip"
```

## Project Structure

*   `src/`: Source code.
    *   `core/`: Core logic for video processing, audio analysis, and AI scoring.
    *   `ui/`: Streamlit user interface.
    *   `utils/`: Helper functions.
*   `bg_music/`: Folder for storing background music tracks.
*   `input/`: Default folder for input media (optional).

## Troubleshooting

*   **"MoviePy error: FFMPEG..."**: Ensure FFmpeg is installed and accessible in your system PATH.
*   **Slow Processing**: AI scoring can be slow on CPU. Ensure you have a CUDA-capable GPU and PyTorch is installed with CUDA support for best performance.

## License

MIT
