import os
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import cv2
import numpy as np
from typing import List, Tuple

class VideoScorer:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Check for local model
        local_path = os.path.join("models", model_name)
        if os.path.exists(local_path):
            print(f"Loading local AI Model from {local_path} on {self.device}...")
            load_path = local_path
        else:
            print(f"Loading AI Model ({model_name}) from Hub on {self.device}...")
            load_path = model_name

        self.model = CLIPModel.from_pretrained(load_path).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(load_path)
        print("Model loaded.")

    def score_frame(self, frame: np.ndarray, text_prompts: List[str]) -> float:
        """
        Scores a single frame against a list of positive prompts.
        Returns the maximum similarity score.
        """
        image = Image.fromarray(frame)
        inputs = self.processor(text=text_prompts, images=image, return_tensors="pt", padding=True).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image  # this is the image-text similarity score
            probs = logits_per_image.softmax(dim=1)
            
        # Return the sum of probabilities for the positive prompts
        # Or just the raw logit if we want absolute similarity
        return probs.max().item()

    def analyze_video(self, video_path: str, interval_sec: float = 1.0, max_frames: int = 100, 
                     downsample_resolution: int = 480) -> List[Tuple[float, float]]:
        """
        Analyzes a video and returns a list of (timestamp, score) tuples.
        
        Memory optimizations:
        - Limits total frames analyzed to max_frames
        - Downsamples frames to reduce memory footprint
        - Clears GPU cache after processing
        
        Args:
            video_path: Path to video file
            interval_sec: Interval between analyzed frames in seconds
            max_frames: Maximum number of frames to analyze (default: 100)
            downsample_resolution: Target height for frame downsampling (default: 480)
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        scores = []
        
        # Prompts to identify "good" content
        prompts = ["a photo of a happy family", "a beautiful landscape", "people smiling", "clear and bright image"]
        
        # Calculate sampling strategy
        frames_to_analyze = min(max_frames, int(duration / interval_sec))
        if frames_to_analyze < int(duration / interval_sec):
            # Need to skip more frames to stay under max_frames limit
            actual_interval = duration / frames_to_analyze
            print(f"Analyzing {video_path} ({duration:.1f}s) - sampling {frames_to_analyze} frames (every {actual_interval:.1f}s)...")
        else:
            actual_interval = interval_sec
            print(f"Analyzing {video_path} ({duration:.1f}s) - sampling every {interval_sec:.1f}s...")
        
        current_frame = 0
        frames_analyzed = 0
        
        while cap.isOpened() and frames_analyzed < frames_to_analyze:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process every Nth frame (based on actual interval)
            timestamp = current_frame / fps
            if current_frame % int(fps * actual_interval) == 0:
                # Downsample frame to reduce memory usage
                h, w = frame.shape[:2]
                if h > downsample_resolution:
                    scale = downsample_resolution / h
                    new_w = int(w * scale)
                    frame = cv2.resize(frame, (new_w, downsample_resolution))
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                score = self.score_frame(frame_rgb, prompts)
                scores.append((timestamp, score))
                frames_analyzed += 1
                
                # Release frame memory immediately
                del frame_rgb
                
            current_frame += 1
            
        cap.release()
        
        # Clear GPU cache if using CUDA
        if self.device == "cuda":
            torch.cuda.empty_cache()
        
        return scores

