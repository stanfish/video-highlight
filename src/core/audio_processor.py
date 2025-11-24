import librosa
import numpy as np
from typing import List
import scipy.signal

# Monkey patch for scipy >= 1.13
if not hasattr(scipy.signal, 'hann'):
    try:
        scipy.signal.hann = scipy.signal.windows.hann
    except AttributeError:
        pass # If windows doesn't exist either, we might be in trouble or on very old scipy

class AudioProcessor:
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.y = None
        self.sr = None
        self.duration = 0
        self.beats = []
        
    def load_audio(self):
        """Loads the audio file."""
        print(f"Loading audio: {self.audio_path}...")
        self.y, self.sr = librosa.load(self.audio_path)
        self.duration = librosa.get_duration(y=self.y, sr=self.sr)
        print(f"Audio loaded. Duration: {self.duration:.2f}s")

    def detect_beats(self) -> np.ndarray:
        """Detects beats in the audio and returns their timestamps."""
        if self.y is None:
            self.load_audio()
            
        print("Detecting beats...")
        tempo, beat_frames = librosa.beat.beat_track(y=self.y, sr=self.sr)
        self.beats = librosa.frames_to_time(beat_frames, sr=self.sr)
        print(f"Detected {len(self.beats)} beats. Tempo: {tempo:.2f} BPM")
        return self.beats

    def get_beat_intervals(self) -> List[float]:
        """Returns the duration between beats."""
        if len(self.beats) == 0:
            self.detect_beats()
        
        # Calculate intervals (diff between consecutive beats)
        intervals = np.diff(self.beats)
        return intervals.tolist()
