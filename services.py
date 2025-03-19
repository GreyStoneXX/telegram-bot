import requests
import sett
import logging
from deep_translator import GoogleTranslator
import speech_recognition as sr
# import io

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Función para traducir al inglés
def translate_to_english(text):
    return GoogleTranslator(source='auto', target='en').translate(text)

# Función para traducir al español
def translate_to_spanish(text):
    return GoogleTranslator(source='en', target='es').translate(text)

def convert_audio_to_text(audio_file):
    # Inicializar el reconocedor de voz
    recognizer = sr.Recognizer()
    
    try:
        # Cargar el archivo de audio en formato WAV
        audio = sr.AudioFile(audio_file)
        
        with audio as source:
            # Escuchar el audio y convertirlo a texto
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='es-ES')  # Puedes cambiar el idioma aquí

            return text
    
    except Exception as e:
        logging.error(f"Error al convertir audio a texto: {str(e)}")
        return "No pude entender el audio."

class DeepSeekChatbot:
    def __init__(self, model_name=sett.model, api_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url

    def send_message(self, message):
        data = {
            "model": self.model_name,
            "prompt": message,
            "stream": False,
            "max_tokens": sett.max_tokens
        }

        try:
            response = requests.post(self.api_url, json=data)
            response.raise_for_status()  # Lanza un error si la solicitud falla

            respuesta = response.json().get("response", "")

            if not respuesta:
                logging.error("Respuesta vacía de DeepSeek.")
                return "Lo siento, no pude generar una respuesta."

            return respuesta

        except requests.exceptions.RequestException as e:
            logging.error(f"Error al comunicarse con DeepSeek: {e}")
            return "Hubo un error al conectar con el servicio."

# Inicializa el chatbot de DeepSeek
chatbot = DeepSeekChatbot()

def deepseek_Response(user_message):
    """Traduce el mensaje, obtiene la respuesta de DeepSeek y la traduce de vuelta a español."""
    message_esp = translate_to_english(user_message.lower())
    response = chatbot.send_message(message_esp)

    # Limpieza de la respuesta
    clean_response = response.replace("<think>", "").replace("</think>", "").replace("\n", "").strip()
    message_eng = translate_to_spanish(clean_response)

    return message_eng

def dividir_respuesta(texto, limite=4096):
    """Divide la respuesta en partes más pequeñas para enviarlas por Telegram si excede el límite de caracteres."""
    partes = []
    while len(texto) > limite:
        corte = texto.rfind(" ", 0, limite)  # Intenta cortar en el último espacio antes del límite
        if corte == -1:
            corte = limite  # Si no hay espacios, corta exactamente en el límite
        partes.append(texto[:corte])
        texto = texto[corte:].strip()
    partes.append(texto)
    return partes

def deepseek_Response_en_partes(user_message):
    """Genera una respuesta con DeepSeek y la divide en partes si es necesario para Telegram."""
    respuesta_completa = deepseek_Response(user_message)  # Usa la función original
    return dividir_respuesta(respuesta_completa)
