from flask import Flask
import threading
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# FLASK TRICK FOR RENDER
app = Flask(__name__)
@app.route('/')
def home(): return "Bot running ✅"
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

# CONFIG
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
SHEET_URL = os.getenv("SHEET_URL")

# GOOGLE SHEETS CONNECT
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).sheet1

PRICES = {'daily': '15,000', 'weekly': '35,000', 'monthly': '70,000'}
DAYS = {'daily': 1, 'weekly': 7, 'monthly': 30}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"Daily - ₦{PRICES['daily']}", callback_data='daily')],
        [InlineKeyboardButton(f"Weekly - ₦{PRICES['weekly']}", callback_data='weekly')],
        [InlineKeyboardButton(f"Monthly - ₦{PRICES['monthly']}", callback_data='monthly')]
    ]
    await update.message.reply_text("👋 Welcome to VIP Predictions!\nChoose a plan:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    plan = query.data
    price = PRICES[plan]
    await query.edit_message_text(
        f"You chose *{plan.upper()}* - ₦{price}\n\n"
        f"Pay to: \nAccount: 8143992377\nBank: Opay\nName: Igbeotumeh Emmanuel Olaonipekun\n"
        f"After payment, send screenshot here. Admin will activate you.",
        parse_mode='Markdown'
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        user_id = int(context.args[0]); plan = context.args[1]
        days = DAYS[plan]; expires = datetime.now() + timedelta(days=days)

        users = sheet.get_all_records()
        for i, u in enumerate(users):
            if str(u['user_id']) == str(user_id):
                sheet.update_cell(i+2, 3, plan)
                sheet.update_cell(i+2, 4, expires.strftime("%Y-%m-%d %H:%M:%S"))
                await update.message.reply_text("User updated!")
                await context.bot.send_message(user_id, f"✅ RENEWED! {plan.upper()} till {expires.date()}")
                return

        sheet.append_row([user_id, "VIP", plan, expires.strftime("%Y-%m-%d %H:%M:%S")])
        await update.message.reply_text("User added!")
        await context.bot.send_message(user_id, f"✅ ACTIVATED! {plan.upper()} till {expires.date()}")
    except:
        await update.message.reply_text("Usage: /approve user_id plan")

async def sendcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    code = " ".join(context.args); now = datetime.now()
    users = sheet.get_all_records(); count = 0
    for u in users:
        try:
            if datetime.strptime(u['expires_at'], "%Y-%m-%d %H:%M:%S") > now:
                await context.bot.send_message(u['user_id'], f"🔥 TODAY'S CODE 🔥\n\n`{code}`", parse_mode='Markdown')
                count += 1
        except: pass
    await update.message.reply_text(f"✅ Sent to {count} active users")

def main():
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button))
    app_bot.add_handler(CommandHandler("approve", approve))
    app_bot.add_handler(CommandHandler("sendcode", sendcode))
    print("Bot is running...")
    app_bot.run_polling()

if __name__ == '__main__': main()
