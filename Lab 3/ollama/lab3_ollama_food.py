#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Food Recommendation Voice Assistant - Raspberry Pi Optimized
Simple voice assistant that recommends food based on your preferences

Tell it what you want (noodles, rice, Japanese, Italian, etc.) and get recommendations!
"""

import speech_recognition as sr
import subprocess
import requests
import json
import sys
import os
import contextlib
import warnings

# Suppress ALL audio-related warnings and errors
warnings.filterwarnings("ignore")
os.environ['ALSA_QUIET'] = '1'
os.environ['PULSE_QUIET'] = '1'
os.environ['ALSA_PCM_CARD'] = 'default'
os.environ['ALSA_MIXER_CARD'] = 'default'

# More aggressive stderr suppression
class DevNull:
    def write(self, msg):
        pass
    def flush(self):
        pass

# Global stderr suppression for audio libraries
def suppress_audio_errors():
    # Redirect stderr globally during imports and audio operations
    original_stderr = sys.stderr
    sys.stderr = DevNull()
    return original_stderr

# Restore stderr when needed
def restore_stderr(original_stderr):
    sys.stderr = original_stderr

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'UTF-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    import codecs
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    # Suppress errors during pyttsx3 import
    original_stderr = suppress_audio_errors()
    import pyttsx3
    restore_stderr(original_stderr)
    TTS_ENGINE = 'pyttsx3'
except ImportError:
    restore_stderr(original_stderr)
    TTS_ENGINE = 'espeak'
    print("Using espeak for TTS")

class FoodRecommendationAssistant:
    def __init__(self, model_name="phi3:mini", ollama_url="http://localhost:11434"):
        # Suppress all audio errors during initialization
        original_stderr = suppress_audio_errors()
        
        self.model_name = model_name
        self.ollama_url = ollama_url
        
        # Initialize speech recognition with suppressed errors
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Setup TTS with suppressed errors
        if TTS_ENGINE == 'pyttsx3':
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 160)
        
        # Restore stderr for important messages
        restore_stderr(original_stderr)
        
        # Test Ollama
        self.test_ollama_connection()
        
        # Quick setup with suppressed audio errors
        print("Quick setup... Please wait.")
        original_stderr = suppress_audio_errors()
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        restore_stderr(original_stderr)
        print("Food assistant ready!")

    def test_ollama_connection(self):
        """Test Ollama connection"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.model_name in model_names:
                    print(f"Connected to {self.model_name}")
                else:
                    if model_names:
                        self.model_name = model_names[0]
                        print(f"Using {self.model_name}")
            else:
                raise Exception("Ollama not responding")
        except Exception as e:
            print(f"Ollama error: {e}")
            print("Start with: ollama serve")
            sys.exit(1)

    def speak(self, text):
        """Text to speech with suppressed errors"""
        clean_text = text.strip()[:150]  # Keep it short
        print(f"Assistant: {clean_text}")
        
        # Suppress all audio output errors
        original_stderr = suppress_audio_errors()
        
        if TTS_ENGINE == 'pyttsx3':
            self.tts_engine.say(clean_text)
            self.tts_engine.runAndWait()
        else:
            subprocess.run(['espeak', '-s', '160', clean_text], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        restore_stderr(original_stderr)

    def listen(self):
        """Listen for speech with suppressed audio errors"""
        try:
            print("Listening...")
            
            # Suppress all audio input errors
            original_stderr = suppress_audio_errors()
            
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
            
            print("Processing...")
            text = self.recognizer.recognize_google(audio)
            
            # Restore stderr after audio operations
            restore_stderr(original_stderr)
            
            print(f"You said: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            restore_stderr(original_stderr)
            print("No speech detected")
            return None
        except sr.UnknownValueError:
            restore_stderr(original_stderr)
            print("Couldn't understand")
            return None
        except sr.RequestError as e:
            restore_stderr(original_stderr)
            print(f"Speech error: {e}")
            return None

    def get_food_recommendation(self, user_input):
        """Get food recommendation from Ollama with ultra-simple prompt for Pi"""
        # Super simple system prompt for Pi performance
        system_prompt = """You are a food assistant. Give 2 quick food suggestions based on what the user wants. Be brief."""
        
        try:
            # Ultra-minimal prompt for faster processing
            simple_prompt = f"Suggest food for: {user_input[:20]}"  # Limit input length too
            
            data = {
                "model": self.model_name,
                "prompt": simple_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 80,  # Very short responses
                    "top_k": 10,       # Limit choices for speed
                    "top_p": 0.8       # More focused responses
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=30  # Keep your 30 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'How about noodles or rice?')
            else:
                return "Maybe try some pasta or fried rice?"
                
        except requests.exceptions.Timeout:
            return "Pi is slow today. How about pizza or noodles?"
        except Exception as e:
            return "Error occurred. Maybe some soup or sandwich?"

    def show_help(self):
        """Show help"""
        print("\nFood Recommendation Assistant")
        print("Just tell me what you want to eat!")
        print("Examples:")
        print("- 'I want noodles'")
        print("- 'Something Japanese'")
        print("- 'Rice dishes'")
        print("- 'Italian food'")
        print("- 'Something light'")
        print("- 'Comfort food'")
        print("\nSay 'quit' to exit")

    def run_conversation(self):
        """Main conversation loop"""
        print("=" * 40)
        print("FOOD RECOMMENDATION ASSISTANT")
        print("=" * 40)
        self.show_help()
        print("=" * 40)
        
        self.speak("Hi! I am your food recommendation assistant. What would you like to eat today?")
        
        while True:
            try:
                user_input = self.listen()
                
                if user_input is None:
                    continue
                
                # Handle exit commands
                if any(word in user_input for word in ['exit', 'quit', 'bye', 'goodbye']):
                    self.speak("Enjoy your meal! See you next time!")
                    break
                
                # Handle help
                if 'help' in user_input:
                    self.show_help()
                    continue
                
                # Handle greetings
                if any(word in user_input for word in ['hello', 'hi', 'hey']):
                    self.speak("Hello! What kind of food are you in the mood for?")
                    continue
                
                # Get food recommendation
                print("Thinking of delicious options...")
                recommendation = self.get_food_recommendation(user_input)
                self.speak(recommendation)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                self.speak("Goodbye! Enjoy your meal!")
                break
            except Exception as e:
                print(f"Error: {e}")
                self.speak("Sorry, I had a small problem. What food were you thinking about?")

def main():
    """Main function"""
    print("Starting Food Recommendation Assistant...")
    
    # Check dependencies
    try:
        import speech_recognition
        import requests
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install speechrecognition requests pyaudio")
        return
    
    # Run assistant
    try:
        assistant = FoodRecommendationAssistant()
        assistant.run_conversation()
    except Exception as e:
        print(f"Startup error: {e}")

if __name__ == "__main__":
    main()