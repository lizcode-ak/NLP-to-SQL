import base64
import requests
import json
import sys
from config import Config

class VisionProcessor:
    def __init__(self):
        self.ollama_url = Config.OLLAMA_URL
        self.model = "llava" # Dedicated vision model

    def analyze_image(self, image_path, prompt=None):
        """Analyze image using Ollama Vision API"""
        try:
            if not prompt:
                prompt = "Describe this image in detail. If it contains a table or chart, summarize the data columns and rows."

            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "images": [base64_image],
                "options": {
                    "temperature": 0.0
                }
            }

            sys.stderr.write(f"DEBUG: Calling Ollama Vision with model '{self.model}'\n")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=300
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', '').strip()
                return {'success': True, 'analysis': analysis}
            
            return {
                'success': False, 
                'error': f"Ollama Vision API error: {response.status_code}"
            }
        except Exception as e:
            sys.stderr.write(f"DEBUG: Vision analysis failed: {str(e)}\n")
            return {'success': False, 'error': str(e)}
