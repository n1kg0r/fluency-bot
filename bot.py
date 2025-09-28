import os
import asyncio
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from llm_client import ask_llm, SESSIONS

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in SESSIONS:
        del SESSIONS[user_id]
    await update.message.reply_text(
        "👋 Hi! I'm Language Penpal Bot\nWhich language would you like to practice?\n\n"
        "Just type the name (e.g. 'French', 'Italian', 'Spanish')."
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()


    for exit_prompt in ["bye", "ok i need to go", "see you", "ciao", "/exit"]:
        if exit_prompt in text.lower():
            msg = await ask_llm(user_id, text, mode="exit")
            await update.message.reply_text(msg)
            if user_id in SESSIONS:
                del SESSIONS[user_id]
            return

    if user_id not in SESSIONS:
        SESSIONS[user_id] = {
            "target_lang": text,
            "messages": [],
            "last_ts": time.time(),
        }
        msg = await ask_llm(user_id, "", mode="presentation", target_l=text)
        await update.message.reply_text(msg)
        return

    msg = await ask_llm(user_id, text, mode="interaction")
    await update.message.reply_text(msg)

async def idle_checker(app: Application):
    while True:
        now = time.time()
        for user_id, sess in list(SESSIONS.items()):
            if now - sess["last_ts"] > 5 * 3600: 
                sess["last_ts"] = now 
                try:
                    msg = await ask_llm(user_id, "It's been a while!", mode="interaction")
                    await app.bot.send_message(user_id, msg)
                except Exception as e:
                    print("idle send error:", e)
        await asyncio.sleep(300)  

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app.job_queue.run_repeating(lambda _: asyncio.create_task(idle_checker(app)), interval=3600, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()