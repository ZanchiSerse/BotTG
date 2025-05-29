import logging
import requests
import json
import random
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Percorso del file delle barzellette
JOKES_FILE = "barzellette.json"

# Funzione per caricare le barzellette dal file
def load_jokes():
    if os.path.exists(JOKES_FILE):
        with open(JOKES_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        # File predefinito se non esiste
        default_jokes = {
            "barzellette": [
                "Qual è la città preferita dai ragni? Mosca!",
                "Cosa fa un cammello in acqua? Si scioglie!",
                "Un pomodoro va dal dottore. Il dottore: 'Ti vedo un po' rosso, sei sicuro di stare bene?'"
            ]
        }
        with open(JOKES_FILE, 'w', encoding='utf-8') as file:
            json.dump(default_jokes, file, ensure_ascii=False, indent=4)
        return default_jokes

# Funzione per ottenere una barzelletta dall'API Barzette.NET
def get_joke_from_api():
    try:
        # API per barzellette italiane
        response = requests.get("https://api.barzellette.net/v1/random/")
        
        if response.status_code == 200:
            data = response.json()
            if "text" in data:
                return {"source": "API", "joke": data["text"]}
    except Exception as e:
        logger.error(f"Errore API Barzellette.NET: {e}")
    
    try:
        # Piano B: Prova con l'API Spillo.dev per barzellette italiane
        response = requests.get("https://v1.spillo.dev/api/jokes/random")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "joke" in data["data"]:
                return {"source": "API", "joke": data["data"]["joke"]}
    except Exception as e:
        logger.error(f"Errore API Spillo: {e}")
    
    try:
        # Piano C: API JokeAPI cercando solo barzellette italiane
        response = requests.get(
            "https://v2.jokeapi.dev/joke/Any",
            params={"format": "json", "lang": "it"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "joke" in data:
                return {"source": "API", "joke": data["joke"]}
            elif "setup" in data and "delivery" in data:
                return {"source": "API", "joke": f"{data['setup']}\n\n{data['delivery']}"}
    except Exception as e:
        logger.error(f"Errore JokeAPI: {e}")
    
    # Se tutte le API falliscono, usiamo le barzellette locali
    jokes_data = load_jokes()
    return {"source": "Locale", "joke": random.choice(jokes_data["barzellette"])}

# Ottieni barzelletta dal file locale
def get_joke_from_file():
    jokes_data = load_jokes()
    return {"source": "Locale", "joke": random.choice(jokes_data["barzellette"])}

# Comando /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Barzelletta dall'API", callback_data="api"),
            InlineKeyboardButton("Barzelletta Locale", callback_data="local")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Ciao! Sono il tuo bot delle barzellette! 😄\n\n'
        'Usa /barzelletta per ricevere una barzelletta da fonti online (API).\n'
        'Usa /locale per ricevere una barzelletta dal file locale.\n'
        'Usa /help per vedere tutti i comandi disponibili.',
        reply_markup=reply_markup
    )

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Comandi disponibili:\n'
        '/start - Inizia la conversazione\n'
        '/barzelletta - Ricevi una barzelletta da API online\n'
        '/locale - Ricevi una barzelletta dal file locale\n'
        '/help - Mostra questo messaggio'
    )

# Comando /barzelletta (API)
async def barzelletta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_joke_from_api()
    await update.message.reply_text(f"{result['joke']}\n\n[Fonte: {result['source']}]")

# Comando /locale (File)
async def locale_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_joke_from_file()
    await update.message.reply_text(f"{result['joke']}\n\n[Fonte: {result['source']}]")

# Gestione callback per i pulsanti
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "api":
        result = get_joke_from_api()
        await query.message.reply_text(f"{result['joke']}\n\n[Fonte: {result['source']}]")
    elif query.data == "local":
        result = get_joke_from_file()
        await query.message.reply_text(f"{result['joke']}\n\n[Fonte: {result['source']}]")

# Aggiungi questo prima della definizione della funzione main()
def run_bot_with_retry():
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            main()
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Errore nel bot: {e}. Tentativo di riavvio {retry_count}/{max_retries}")
            time.sleep(10)  # Attendi 10 secondi prima di riavviare

def main():
    # Token del bot Telegram
    TOKEN = "7932854606:AAFeEwPGQi2WEWgft_mz-s-bq--JuFjG4ao"  # Il tuo token attuale
    
    application = Application.builder().token(TOKEN).build()

    # Aggiungi i gestori dei comandi
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("barzelletta", barzelletta_command))
    application.add_handler(CommandHandler("locale", locale_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Avvia il Bot
    logger.info("Bot avviato! Premi Ctrl+C per terminare.")
    application.run_polling()

if __name__ == '__main__':
    run_bot_with_retry()