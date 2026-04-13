import re
import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8670650230:AAHFFLv9qBy8nEHVZrcPJAo7AeFj1VvdT7A"

# --- російський детектор ---
ru_pattern = re.compile(r"[ыэёъ]")

ru_words_strict = [
    "что", "это", "как", "почему", "зачем",
    "где", "когда", "привет", "вообще",
    "конечно", "нельзя", "сейчас", "только"
]

UA_ONLY_TEXT = (
    "⛔ У цьому чаті спілкування тільки українською мовою.\n\n"
    "Мут на 3 хвилини."
)

CHAT_ID = None


# --- мут (строго 3 хвилини) ---
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE, minutes=3):
    try:
        until = int(
            (datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)).timestamp()
        )

        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            permissions={"can_send_messages": False},
            until_date=until
        )
    except Exception as e:
        print(e)


# --- команди ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот працює")


async def setchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    await update.message.reply_text(f"Чат збережено: {CHAT_ID}")


# --- щоденне повідомлення ---
async def daily_message(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID:
        await context.bot.send_message(chat_id=CHAT_ID, text="📌 Спілкування українською мовою")


# --- фільтр ---
async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()

    # --- детектор ---
    ru_score = 0

    # російські букви
    if ru_pattern.search(text):
        ru_score += 1

    # російські слова
    words = re.findall(r"\b\w+\b", text)
    ru_score += sum(1 for word in words if word in ru_words_strict)

    # --- мут тільки якщо впевнені ---
    if ru_score >= 2:
        await update.message.reply_text(UA_ONLY_TEXT)
        await mute_user(update, context, 3)
        return


# --- запуск ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setchat", setchat))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_messages))

    app.job_queue.run_daily(
        daily_message,
        time=datetime.time(hour=12, minute=0)
    )

    print("Бот запущений")
    app.run_polling()


if __name__ == "__main__":
    main()