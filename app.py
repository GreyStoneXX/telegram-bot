from flask import Flask, request
import services
import sett
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackContext
from pydub import AudioSegment
import speech_recognition as sr
import asyncio
import os

app = Flask(__name__)

# Configurar logs para depuración
logging.basicConfig(level=logging.INFO)

@app.route('/bienvenido', methods=['GET'])
def bienvenido():
    return 'Felicidades, tu servidor está funcionando desde Flask con Telegram'

# Función para convertir audio en formato .ogg a texto de forma asíncrona
async def convert_audio_to_text(audio_path):
    try:
        # Convertir .ogg a .wav utilizando pydub en un hilo separado para evitar bloqueo
        loop = asyncio.get_running_loop()
        audio = await loop.run_in_executor(None, AudioSegment.from_ogg, audio_path)

        # Exportar el archivo a formato .wav
        wav_path = "temp_audio.wav"
        await loop.run_in_executor(None, audio.export, wav_path, "wav")

        # Usar speech_recognition para convertir el archivo .wav a texto en un hilo separado
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = await loop.run_in_executor(None, recognizer.record, source)

        # Realizar el reconocimiento de voz de forma asíncrona
        text = await loop.run_in_executor(None, recognizer.recognize_google, audio_data)

        # Eliminar el archivo temporal después de procesarlo
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

        # Obtener respuesta dividida en partes usando procesamiento asíncrono
        response = services.deepseek_Response_en_partes(user_message)

        # Enviar cada parte de la respuesta de forma asíncrona
        for part in response:
            if len(part) > 5000:
                logging.error(f"El mensaje de respuesta es demasiado largo: {len(part)} caracteres.")
                await context.bot.send_message(chat_id=chat_id, text="Lo siento, la respuesta es demasiado larga para enviarla.")
                return
            await context.bot.send_message(chat_id=chat_id, text=part)

    except Exception as e:
        logging.error(f"Error al procesar mensaje: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text="Hubo un error al procesar tu solicitud. Aun estoy en desarrollo.")

# Función para manejar mensajes de audio de forma asíncrona
async def recibir_audio(update: Update, context: CallbackContext):
    try:
        chat_id = update.message.chat_id
        audio = update.message.voice
        file_id = audio.file_id
        file = await context.bot.get_file(file_id)

        # Descargar el archivo de audio como bytearray de forma asíncrona
        audio_data = await file.download_as_bytearray()

        # Guardar el archivo temporal
        temp_audio_path = "temp_audio.ogg"
        with open(temp_audio_path, 'wb') as f:
            f.write(audio_data)

        # Convertir audio a texto de forma asíncrona
        user_message = await convert_audio_to_text(temp_audio_path)

        if not user_message:
            await context.bot.send_message(chat_id=chat_id, text="Lo siento, no pude entender el audio. Aun estoy en desarrollo")
            os.remove(temp_audio_path)
            return

        # Procesar el mensaje de texto de manera asíncrona
        logging.info(f"Mensaje de audio convertido: {user_message}")
        response = services.deepseek_Response_en_partes(user_message)

        # Enviar la respuesta de la IA de forma asíncrona
        for part in response:
            await context.bot.send_message(chat_id=chat_id, text=part)

        # Eliminar el archivo temporal
        os.remove(temp_audio_path)

    except Exception as e:
        logging.error(f"Error al procesar audio: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text="Lo siento, hubo un error al procesar el audio.")

# Iniciar el bot de Telegram
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("¡Hola! Soy tu asistente. Envíame un mensaje y te responderé.")

# Función principal para iniciar el bot
def iniciar_bot():
    application = Application.builder().token(sett.telegram_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_mensaje))
    application.add_handler(MessageHandler(filters.VOICE, recibir_audio))
    application.run_polling()

if __name__ == '__main__':
    iniciar_bot()
