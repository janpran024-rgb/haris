import asyncio
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Credentials
BOT_TOKEN = "8896684220:AAHiL6ZA_7_mOe0FSAW5x5eqUV3D2Ob0LXs"
ADMIN_USERNAME = "hiba5858"
DB_URL = "https://hafi-hiba-default-rtdb.firebaseio.com/"

# Web server to satisfy Render's HTTP Port requirement
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Telegram Bot is Live!")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        await update.message.reply_text("❌ আপনার এই এডমিন প্যানেল ব্যবহারের অনুমতি নেই।")
        return

    keyboard = [
        [InlineKeyboardButton("💳 উইথড্র রিকোয়েস্ট চেক করুন", callback_data="check_withdraw")],
        [InlineKeyboardButton("📊 মোট ইউজার সংখ্যা", callback_data="total_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 স্বাগতম এডমিন প্যানেলে!", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_withdraw":
        try:
            res = requests.get(f"{DB_URL}/withdrawals.json").json()
            if not res:
                await query.edit_message_text("বর্তমানে কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই।")
                return

            text = "📋 **পেন্ডিং উইথড্র তালিকা:**\n\n"
            has_pending = False
            for key, value in res.items():
                if isinstance(value, dict) and value.get("status") == "Pending":
                    has_pending = True
                    text += f"👤 নাম: {value.get('name')}\n📱 {str(value.get('method')).upper()}: {value.get('phone')}\n💰 পরিমাণ: ৳{value.get('amount')}\n--------------------\n"
            
            if not has_pending:
                text = "বর্তমানে কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই।"

            await query.edit_message_text(text, parse_mode="Markdown")
        except Exception:
            await query.edit_message_text("ডাটা লোড করতে সমস্যা হয়েছে।")

    elif query.data == "total_users":
        try:
            res = requests.get(f"{DB_URL}/users.json").json()
            total = len(res) if res else 0
            await query.edit_message_text(f"👥 মোট রেজিস্টার্ড ইউজার: {total} জন")
        except Exception:
            await query.edit_message_text("ইউজার তথ্য পাওয়া যায়নি।")

def main():
    # Start HTTP server in a separate thread for Render health check
    threading.Thread(target=run_http_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()

if __name__ == "__main__":
    main()
  
