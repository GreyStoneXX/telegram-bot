from flask import Flask, request
import services
import subprocess
import time
import sett
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackContext

app = Flask(__name__)

# Función para iniciar el servidor de DeepSeek usando ollama
def start_deepseek_server():
    deepseek_server_command = ["ollama", "run", sett.model]
    subprocess.Popen(deepseek_server_command)
    # Espera unos segundos para asegurarte de que el servidor se inicie correctamente
    time.sleep(5)

# Configurar logs para depuración
logging.basicConfig(level=logging.INFO)

@app.route('/bienvenido', methods=['GET'])
def bienvenido():
    return 'Felicidades, tu servidor está funcionando desde Flask con Telegram'

# Función para manejar mensajes en Telegram
async def recibir_mensaje(update: Update, context: CallbackContext):
    try:
        chat_id = update.message.chat_id
        user_message = update.message.text
        logging.info(f"Mensaje recibido de {chat_id}: {user_message}")

        # Responder con el modelo de IA
        response = services.deepseek_Response(user_message)
        
        # Enviar respuesta a Telegram
        await context.bot.send_message(chat_id=chat_id, text=response)

    except Exception as e:
        logging.error(f"Error al procesar mensaje: {str(e)}")

# Iniciar el bot de Telegram
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("¡Hola! Soy tu asistente. Envíame un mensaje y te responderé.")

def iniciar_bot():
    application = Application.builder().token(sett.telegram_token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_mensaje))
    
    application.run_polling()

if __name__ == '__main__':
    # Inicia el servidor de DeepSeek
    start_deepseek_server()
     # Inicia la aplicación
    iniciar_bot()
