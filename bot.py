import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from datetime import datetime
import time
import sys
import asyncio

TOKEN = "your_bot_token"
SUPPORT_GROUP_ID = -1000000000000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tickets = {}

async def safe_call(bot, func_name: str, *args, retries: int = 3, delay: int = 2, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            func = getattr(bot, func_name)
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == retries: return None
            await asyncio.sleep(delay * attempt)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private": return
    await update.message.reply_text("مرحباً بك في نظام الدعم. استخدم /ticket لفتح تذكرة جديدة.")

async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private": return
    user = update.effective_user
    ticket_id = f"T-{user.id}-{int(time.time())}"
    
    msg = f"📩 تذكرة جديدة من {user.full_name} (@{user.username})\nID: {user.id}\nالوقت: {datetime.now()}"
    topic = await safe_call(context.bot, "create_forum_topic", chat_id=SUPPORT_GROUP_ID, name=f"Support: {user.first_name}")
    
    if topic:
        tickets[user.id] = {"group_id": SUPPORT_GROUP_ID, "topic_id": topic.message_thread_id}
        await safe_call(context.bot, "send_message", chat_id=SUPPORT_GROUP_ID, text=msg, message_thread_id=topic.message_thread_id)
        await update.message.reply_text("تم فتح تذكرة لك. يمكنك إرسال رسالتك هنا وسيرد عليك الدعم.")

async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in tickets:
        del tickets[user_id]
        await update.message.reply_text("تم إغلاق التذكرة.")

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.type == "private":
        if message.from_user.id in tickets:
            info = tickets[message.from_user.id]
            await safe_call(context.bot, "copy_message", chat_id=info["group_id"], from_chat_id=message.chat_id, message_id=message.message_id, message_thread_id=info["topic_id"])
    elif message.chat.id == SUPPORT_GROUP_ID and message.reply_to_message:
        ticket_user = next((uid for uid, info in tickets.items() if info["topic_id"] == message.message_thread_id), None)
        if ticket_user:
            await safe_call(context.bot, "copy_message", chat_id=ticket_user, from_chat_id=message.chat_id, message_id=message.message_id)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ticket", ticket_command))
    app.add_handler(CommandHandler("close", close_command))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_reply))
    app.run_polling()

if __name__ == '__main__':
    main()
