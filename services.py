import requests
# import json
import sett
# import logging
from deep_translator import GoogleTranslator
# from transformers import pipeline

# Cargar el modelo de resumen
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Función para traducir al inglés
def translate_to_english(text):
    return GoogleTranslator(source='auto', target='en').translate(text)

# Función para traducir al español
def translate_to_spanish(text):
    return GoogleTranslator(source='en', target='es').translate(text)

class DeepSeekChatbot:
    def __init__(self, model_name=sett.model, api_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url

    def send_message(self, message):
        data = {
            "model": self.model_name,
            "prompt": message,
            "temperature": sett.temperature,
            "stream": False
        }

        response = requests.post(self.api_url, json=data)

        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: {response.status_code}, {response.text}"

# Inicializa el chatbot de DeepSeek
chatbot = DeepSeekChatbot()

def deepseek_Response(user_message):
    message_esp = translate_to_english(user_message.lower())
    response = chatbot.send_message(message_esp)
    
    # Limpieza de respuesta
    clean_response = response.replace("<think>", "").replace("</think>", "").replace("\n", "").strip()
    message_eng = translate_to_spanish(clean_response)
    # resumen = summarizer(clean_response, max_length=150, min_length=50, do_sample=False)
    # return resumen[0]['summary_text']

    return message_eng
