import os
from transformers import CLIPProcessor, CLIPModel

def download_model():
    model_name = "openai/clip-vit-base-patch32"
    local_dir = os.path.join("models", model_name)
    
    print(f"Downloading {model_name} to {local_dir}...")
    
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
        
    try:
        model = CLIPModel.from_pretrained(model_name)
        model.save_pretrained(local_dir)
        
        processor = CLIPProcessor.from_pretrained(model_name)
        processor.save_pretrained(local_dir)
        
        print("Download complete!")
    except Exception as e:
        print(f"Failed to download model: {e}")

if __name__ == "__main__":
    download_model()
