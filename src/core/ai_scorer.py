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

    def analyze_video(self, video_path: str, interval_sec: float = 1.0) -> List[Tuple[float, float]]:
        """
        Analyzes a video and returns a list of (timestamp, score) tuples.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        scores = []
        
        # Prompts to identify "good" content
        prompts = ["a photo of a happy family", "a beautiful landscape", "people smiling", "clear and bright image"]
        
        print(f"Analyzing {video_path} ({duration:.1f}s)...")
        
        current_frame = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process every Nth frame (based on interval)
            timestamp = current_frame / fps
            if current_frame % int(fps * interval_sec) == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                score = self.score_frame(frame_rgb, prompts)
                scores.append((timestamp, score))
                
            current_frame += 1
            
        cap.release()
        return scores
