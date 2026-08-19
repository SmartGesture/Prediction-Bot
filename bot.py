from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from datetime import datetime, timedelta
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

conn = sqlite3.connect('predict_bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
            (user_id INTEGER, name TEXT, plan TEXT, expires_at TEXT, PRIMARY KEY(user_id))''')
conn.commit()

PRICES = {'daily': 1, 'weekly': 7, 'monthly': 30}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Daily - ₦35,000", callback_data='daily')],
        [InlineKeyboardButton("Weekly - ₦50,000", callback_data='weekly')],
        [InlineKeyboardButton("Monthly - ₦100,000", callback_data='monthly')]
    ]
    await update.message.reply_text(
        "👋 Welcome to VIP Predictions Bot!\n\nGet daily prediction codes here.\nChoose a plan:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    plan = query.data
    price = {'daily': '15,000', 'weekly': '35,000', 'monthly': '70,000'}[plan]
    await query.edit_message_text(
        f"You chose *{plan.upper()}* - ₦{price}\n\n"
        f"Pay to: \nAccount: 0123456789\nBank: YOUR BANK\nName: YOUR NAME\n"
        f"After payment, send screenshot here. Admin will activate you.",
        parse_mode='Markdown'
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    user_id = int(context.args[0])
    plan = context.args[1]
    days = PRICES[plan]
    expires = datetime.now() + timedelta(days=days)
    c.execute("REPLACE INTO users VALUES (?,?,?,?)",
              (user_id, "User", plan, expires.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    await context.bot.send_message(user_id, f"✅ You are ACTIVE on {plan.upper()} till {expires.date()}")
    await update.message.reply_text("User activated!")

async def sendcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    code = " ".join(context.args)
    now = datetime.now()
    c.execute("SELECT user_id FROM users WHERE expires_at >?", (now,))
    users = c.fetchall()
    count = 0
    for user_id, in users:
        try:
            await context.bot.send_message(user_id, f"🔥 TODAY'S CODE 🔥\n\n`{code}`", parse_mode='Markdown')
            count += 1
        except: pass
    await update.message.reply_text(f"✅ Sent to {count} active users")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("sendcode", sendcode))
app.run_polling()
