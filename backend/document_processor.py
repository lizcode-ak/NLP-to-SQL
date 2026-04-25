import os
import speech_recognition as sr
from pydub import AudioSegment

class DocumentProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def extract_text_from_txt(self, file_path):
        """Read text from a .txt file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read text file: {e}")

    def transcribe_audio(self, file_path):
        """Transcribe audio file to text using Google Web Speech API"""
        try:
            # If mp3, convert to wav first
            if file_path.lower().endswith('.mp3'):
                wav_path = file_path.replace('.mp3', '.wav')
                audio = AudioSegment.from_mp3(file_path)
                audio.export(wav_path, format="wav")
                target_path = wav_path
            else:
                target_path = file_path

            # Load audio file
            with sr.AudioFile(target_path) as source:
                audio_data = self.recognizer.record(source)

            # Transcribe (requires internet connection for Google API)
            text = self.recognizer.recognize_google(audio_data)
            
            # Cleanup temporary wav file if we created one
            if file_path.lower().endswith('.mp3') and os.path.exists(target_path):
                os.remove(target_path)
                
            return text
        except sr.UnknownValueError:
            raise Exception("Speech Recognition could not understand the audio.")
        except sr.RequestError as e:
            raise Exception(f"Could not request results from Speech Recognition service; {e}")
        except Exception as e:
            raise Exception(f"Failed to process audio file: {e}")
