import os
import re
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from openai import AsyncOpenAI
import httpx

# Загрузка переменных окружения
load_dotenv()

# Инициализация клиентов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://srv896150.hstgr.cloud/")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
user_data = {}

# Константы
HEBREW_GREETING = "שלום! אני הבוט שלך ללימוד עברית. שלח לי הודעת קול ואני אעזור לך."
HELP_TEXT = """
📚 *Помощь по боту:*

1. Просто отправьте голосовое сообщение на иврите, и бот ответит вам
2. Используйте кнопку "📖 Открыть словарь" для анализа текста
3. Команды:
   /start - начать работу с ботом
   /help - показать это сообщение

Бот поможет вам практиковать разговорный иврит!
"""
VOICE_MODEL_ID = "21m00Tcm4TlvDq8ikWAM"

async def generate_voice(text: str) -> bytes:
    """Генерация голосового сообщения"""
    if not ELEVENLABS_API_KEY:
        return None
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_MODEL_ID}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.8
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            return response.content
    except Exception as e:
        print(f"Ошибка генерации голоса: {str(e)}")
        return None

async def send_voice_message(chat_id: int, context: ContextTypes.DEFAULT_TYPE, text: str, caption: str):
    """Отправка голосового сообщения с кнопками"""
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]["last_response"] = text
    
    await context.bot.send_chat_action(chat_id=chat_id, action="record_voice")
    
    audio_data = await generate_voice(text)
    if not audio_data:
        return await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔊 {caption}\n\n{text}",
            reply_markup=get_help_keyboard(text)
        )
    
    try:
        with open("temp_voice.mp3", "wb") as f:
            f.write(audio_data)

        await context.bot.send_voice(
            chat_id=chat_id,
            voice=open("temp_voice.mp3", "rb"),
            caption=caption,
            reply_markup=get_help_keyboard(text)
        )
    finally:
        if os.path.exists("temp_voice.mp3"):
            os.remove("temp_voice.mp3")

def get_help_keyboard(text: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками помощи и словаря"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Открыть словарь", web_app=WebAppInfo(url=f"{MINI_APP_URL}?text={quote(text)}")),
            InlineKeyboardButton("🆘 Помощь", callback_data="help")
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Добро пожаловать в бота для изучения иврита! Отправьте голосовое сообщение на иврите.",
        reply_markup=get_help_keyboard(HEBREW_GREETING)
    )
    await send_voice_message(
        update.message.chat_id,
        context,
        HEBREW_GREETING,
        "👋 Приветствие"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=get_help_keyboard(HELP_TEXT)
    )

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопки помощи"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=get_help_keyboard(HELP_TEXT)
    )

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    if not update.message.voice:
        return

    voice_file = await update.message.voice.get_file()
    voice_path = "temp_voice.ogg"
    await voice_file.download_to_drive(voice_path)
    
    try:
        with open(voice_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                language="he"
            )
        user_text = transcription.text
    except Exception as e:
        print(f"Ошибка распознавания: {e}")
        await update.message.reply_text("⚠️ Не удалось распознать речь")
        return
    finally:
        if os.path.exists(voice_path):
            os.remove(voice_path)
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "אתה מורה לעברית. ענה בעברית בצורה ברורה ופשוטה."},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7
        )
        gpt_response = response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка GPT: {e}")
        gpt_response = "סליחה, אני לא מצליח להבין. תוכל לחזור שוב?"
    
    await send_voice_message(
        update.message.chat_id,
        context,
        gpt_response,
        f"🔊 Ответ на: {user_text}"
    )

def main():
    """Запуск бота"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавление обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
    
    app.add_error_handler(lambda u, c: print(f"Ошибка: {c.error}"))

    print("Бот запущен с поддержкой Mini App")
    app.run_polling()

if __name__ == "__main__":
    main()
