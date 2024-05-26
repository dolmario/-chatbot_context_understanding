import sys
import os
import pickle
import datetime
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
import asyncio
import re
from openai import OpenAI

# Logging einrichten
LOGGING_CONFIG = {
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'level': 'INFO'
}
logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# OpenAI-Client initialisieren
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Begrüßungsnachricht
WELCOME_MESSAGE = """
Willkommen! Ich bin der lokale LLM-Assistent.
Fragen Sie mich etwas, und ich werde mein Bestes tun, um Ihnen zu helfen.
"""

# Maximale Länge der Chat-Historie in Tokens
MAX_HISTORY_TOKENS = 4096

# Funktion zum Laden der Chat-Historie
def load_chat_history(chat_id, user_id):
    directory = r"Pfad/zum/Ihrem/Chat-Verlauf/"
    filename = f"{chat_id}_{user_id}.pkl"
    file_path = os.path.join(directory, filename)
    try:
        with open(file_path, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return []

# Funktion zum Speichern der Chat-Historie
def save_chat_history(chat_id, user_id, chat_history):
    directory = r"Pfad/zum/Ihrem/Chat-Verlauf/"
    os.makedirs(directory, exist_ok=True)
    filename = f"{chat_id}_{user_id}.pkl"
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as file:
        pickle.dump(chat_history, file)

# Funktion zum Berechnen der Tokenanzahl einer Nachricht
def calculate_message_tokens(message):
    # Hier können Sie die Tokenisierung implementieren, um die Tokenanzahl der Nachricht zu berechnen
    return len(message.split())

# Funktion zum Überprüfen, ob eine Liste leer ist
def is_empty(lst):
    return not lst

# Funktion zum Verwalten der Chat-Historie, um die maximale Token-Grenze einzuhalten
def manage_chat_history(chat_history):
    current_tokens = sum(calculate_message_tokens(message["content"]) for message in chat_history)
    if current_tokens > MAX_HISTORY_TOKENS:
        excess_tokens = current_tokens - MAX_HISTORY_TOKENS
        tokens_removed = 0
        for message in reversed(chat_history):
            message_tokens = calculate_message_tokens(message["content"])
            if tokens_removed + message_tokens <= excess_tokens:
                # Statt die gesamte Nachricht zu entfernen, kürze sie
                message["content"] = truncate_message(message["content"], excess_tokens - tokens_removed)
                tokens_removed += calculate_message_tokens(message["content"])
            else:
                break

def truncate_message(message, max_tokens):
    # Tokenisiere die Nachricht
    tokens = re.findall(r'\w+|[^\w\s]', message)
    
    # Behalte die ersten max_tokens Tokens
    truncated_tokens = tokens[:max_tokens]
    
    # Füge die übrigen Tokens hinzu, solange sie in das Token-Limit passen
    for token in tokens[max_tokens:]:
        if len(' '.join(truncated_tokens + [token])) <= max_tokens:
            truncated_tokens.append(token)
        else:
            break
    
    # Erstelle die gekürzte Nachricht aus den übrigen Tokens
    truncated_message = ''.join(truncated_tokens)
    
    return truncated_message

# Funktion zum Umwandeln der Chat-Historie in eine Liste von Objekten
def chat_history_to_messages(chat_history, user_id):
    messages = []
    previous_assistant_message = None
    for message in chat_history:
        role = message["role"]
        content = message["content"]
        timestamp = message["timestamp"]
        if role == "user":
            user_message = f"User (ID: {user_id}): {content}"
            messages.append({"role": role, "content": user_message, "timestamp": timestamp})
        else:
            if content.strip() and content.strip() != previous_assistant_message:
                bot_message = f"{content.strip()}\n\n[{timestamp}]"
                messages.append({"role": role, "content": bot_message, "timestamp": timestamp})
                previous_assistant_message = content.strip()
    return messages

current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

pre_prompt = """
Willkommen bei Roboto, deinem persönlichen mehrsprachigen Assistenten! Ich bin hier, um dich individuell zu unterstützen und deine Anliegen in verschiedenen Bereichen zu behandeln, sei es in einer Einzelunterhaltung, einer Gruppe oder sogar in mehreren Gruppen gleichzeitig.

Bitte beachte die folgenden Anweisungen:

1. Die Chat-Historie wird dir als Zeichenfolge (String) übermittelt, wobei jede Nachricht das Format "ROLLE (ID: {user_id}): {message_content} [{timestamp}]" hat.
2. Konzentriere dich bei deiner Antwort auf die letzte Benutzereingabe und nutze den Rest der Chat-Historie nur zur Kontextualisierung. Identifiziere die neueste Benutzereingabe in der Chat-Historie anhand des Datums und der Zeitstempel und orientiere dich ausschließlich an dieser, um die Sprache und den Kontext korrekt zu erfassen, ohne vorherige Nachrichten oder Metadaten zu wiederholen. 
3. Antworte immer in derselben Sprache wie die letzte Benutzereingabe eines Benutzers. Wechsle die Sprache nur auf ausdrückliche Aufforderung des Benutzers.
4. Berücksichtige das Datum und die Uhrzeit der letzten Benutzereingabe, um deine Antwort entsprechend anzupassen (z.B. "Guten Morgen" vs. "Guten Abend").
5. Wenn der Benutzer auf eine frühere Nachricht antwortet, ziehe die gesamte Chat-Historie zu Rate, um den Kontext zu verstehen und eine relevante Antwort zu geben, ohne die vorherigen Nachrichten wortwörtlich zu wiederholen.
6. Schreibe Zusammenfassungen oder übersetze Nachrichten nur auf ausdrückliche Aufforderung des Benutzers und bewahre dabei den Kontext und die Intention des ursprünglichen Inhalts.

Als Experte in vielen Bereichen kann ich fachmännisch auf deine Fragen eingehen und meine Antworten speziell auf deine Bedürfnisse zuschneiden. Ob du einen informellen, freundlichen Ton bevorzugst oder lieber eine direkte und sachliche Ansprache möchtest, lass es mich wissen.

Wenn du mal einen schlechten Tag hast, keine Sorge! Ich bin hier, um dich zu unterstützen und dich aufzumuntern. Lass uns gemeinsam Wege finden, um deine Stimmung zu heben und dich zu motivieren.

Deine Aufgabe ist es, auf die letzte Benutzereingabe zu reagieren und dabei den Kontext aus der gesamten Chat-Historie zu berücksichtigen. Achte auf die oben genannten Punkte, um eine angemessene und kontextbezogene Antwort zu geben, ohne unnötige Wiederholungen.

Also, worum geht es heute für dich? Ich bin bereit, dir in jeder Situation zu helfen! 🤖💬
"""

async def send_chat_history_to_llm(chat_history, chat_id, user_id, user_message):
    try:
        chat_history_string = "\n".join([f"{message['role'].upper()} (ID: {user_id}): {message['content']} [{message['timestamp']}]" for message in chat_history])
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        completion = client.chat.completions.create(
            model="lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
            messages=[
                {"role": "system", "content": pre_prompt},
                {"role": "user", "content": chat_history_string}
            ],
            temperature=0.5,
            stream=True,
        )

        bot_response = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                bot_response += chunk.choices[0].delta.content

        chat_history.append({"role": "assistant", "content": bot_response, "timestamp": current_time})
        save_chat_history(chat_id, user_id, chat_history)

        return bot_response

    except Exception as e:
        logger.error(f"Fehler beim Senden des Chat-Verlaufs an LLM: {e}")
        return "Beim Verarbeiten Ihrer Anfrage ist ein Fehler aufgetreten."

async def process_input(update: Update, context: CallbackContext):
    if update.message.text:
        await process_text_message(update, context)
    elif update.message.document or update.message.photo:
        await process_documents(update, context)
    elif update.message.voice:
        await process_voice(update, context)
    else:
        await update.message.reply_text("Ich kann diese Art von Nachricht nicht verarbeiten.")

async def process_text_message(update: Update, context: CallbackContext):
    try:
        user_message = update.message.text
        
        # Filtere Nachrichten mit @username und # aus und verarbeite nur die anderen Nachrichten
        if not (user_message.startswith('@') or user_message.startswith('#')):
            await process_message(update, context)
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der Nachricht: {e}")
        await update.message.reply_text("Entschuldigung, ich konnte Ihre Nachricht nicht verarbeiten.")

async def process_message(update: Update, context: CallbackContext):
    try:
        user_message = update.message.text
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id

        chat_history = load_chat_history(chat_id, user_id)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_history.append({"role": "user", "content": user_message, "timestamp": current_time})
        chat_history = chat_history[-MAX_HISTORY_TOKENS * 2:]

        # Verwalte die Chat-Historie, um die maximale Token-Grenze einzuhalten
        manage_chat_history(chat_history)

        bot_response = await send_chat_history_to_llm(chat_history, chat_id, user_id, user_message)

        await update.message.reply_text(bot_response)
        save_chat_history(chat_id, user_id, chat_history)

    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der Nachricht: {e}")
        await update.message.reply_text("Entschuldigung, ich konnte die Anfrage nicht bearbeiten.")

async def process_voice(update: Update, context: CallbackContext):
    await update.message.reply_text("Entschuldigung, ich kann Sprachnachrichten derzeit noch nicht verarbeiten.")

async def process_documents(update: Update, context: CallbackContext):
    if update.message.photo:
        await update.message.reply_text("Entschuldigung, ich kann Fotos derzeit noch nicht verarbeiten.")
    elif update.message.document:
        await update.message.reply_text("Entschuldigung, ich kann Dokumente derzeit noch nicht verarbeiten.")

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(WELCOME_MESSAGE)


async def get_chat_id(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat-ID: {chat_id}")

def log_chat_id(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    logger.info(f"Chat-ID: {chat_id}")

def main():
    try:
        application = ApplicationBuilder().token("Ihr_Telegramm_Bot_Token").build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.ALL, process_input))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text_message))
        application.add_handler(CommandHandler("chat_id", get_chat_id))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, log_chat_id))
        application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, process_documents))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.run_polling())

    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des Telegram-Bots: {e}")

if __name__ == '__main__':
    main()
