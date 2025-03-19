from flask import Flask, request
import services
# import subprocess
# import time
import sett
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackContext
from pydub import AudioSegment
import speech_recognition as sr
# import io
import os

app = Flask(__name__)

# Configurar logs para depuración
logging.basicConfig(level=logging.INFO)

@app.route('/bienvenido', methods=['GET'])
def bienvenido():
    return 'Felicidades, tu servidor está funcionando desde Flask con Telegram'

# Función para convertir audio en formato .ogg a texto
def convert_audio_to_text(audio_path):
    try:
        # Convertir .ogg a .wav utilizando pydub
        audio = AudioSegment.from_ogg(audio_path)
        wav_path = "temp_audio.wav"
        audio.export(wav_path, format="wav")

        # Usar speech_recognition para convertir el archivo .wav a texto
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        
        # Realizar el reconocimiento de voz
        text = recognizer.recognize_google(audio_data)
        
        # Eliminar el archivo .wav temporal
        os.remove(wav_path)
        
        return text
    
    except Exception as e:
        logging.error(f"Error al convertir el audio a texto: {str(e)}")
        return ""

# Función para manejar mensajes en Telegram
async def recibir_mensaje(update: Update, context: CallbackContext):
    try:
        chat_id = update.message.chat_id
        user_message = update.message.text
        logging.info(f"Mensaje recibido de {chat_id}: {user_message}")

        # Obtener respuesta dividida en partes
        response = services.deepseek_Response_en_partes(user_message)

        # Enviar cada parte de la respuesta como un mensaje separado
        for part in response:
            if len(part) > 5000:
                logging.error(f"El mensaje de respuesta es demasiado largo: {len(part)} caracteres.")
                await context.bot.send_message(chat_id=chat_id, text="Lo siento, la respuesta es demasiado larga para enviarla.")
                return  # No enviar más respuestas si alguna es demasiado larga
            await context.bot.send_message(chat_id=chat_id, text=part)

    except Exception as e:
        logging.error(f"Error al procesar mensaje: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text="Hubo un error al procesar tu solicitud, por favor intenta más tarde.")

# Función para manejar mensajes de audio
async def recibir_audio(update: Update, context: CallbackContext):
    try:
        chat_id = update.message.chat_id
        audio = update.message.voice  # Obtener el mensaje de audio
        file_id = audio.file_id  # Obtener el ID del archivo de audio
        file = await context.bot.get_file(file_id)  # Obtener el archivo

        # Descargar el archivo de audio a un archivo temporal usando download_as_bytearray()
        audio_data = await file.download_as_bytearray()
        
        # Guardar el archivo en un archivo temporal
        temp_audio_path = "temp_audio.ogg"
        with open(temp_audio_path, 'wb') as f:
            f.write(audio_data)

        # Convertir audio a texto
        user_message = convert_audio_to_text(temp_audio_path)

        if not user_message:
            await context.bot.send_message(chat_id=chat_id, text="Lo siento, no pude entender el audio. Aun estoy en desarrollo")
            os.remove(temp_audio_path)
            return

        # Procesar el mensaje de texto
        logging.info(f"Mensaje de audio convertido: {user_message}")
        response = services.deepseek_Response_en_partes(user_message)
        
        # Enviar la respuesta de la IA
        await context.bot.send_message(chat_id=chat_id, text=response)

        # Eliminar el archivo temporal después de procesarlo
        os.remove(temp_audio_path)

    except Exception as e:
        logging.error(f"Error al procesar audio: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text="Lo siento, hubo un error al procesar el audio.")


# Iniciar el bot de Telegram
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("¡Hola! Soy tu asistente. Envíame un mensaje y te responderé.")

def iniciar_bot():
    application = Application.builder().token(sett.telegram_token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_mensaje))
    application.add_handler(MessageHandler(filters.VOICE, recibir_audio))  # Agregar handler para mensajes de audio

    
    application.run_polling()

if __name__ == '__main__':
    iniciar_bot()
