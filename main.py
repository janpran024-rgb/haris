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
        [InlineKeyboardButton("📊 মোট ইউজার সংখ্যা", callback_data="total_users")],
        [InlineKeyboardButton("⚙️ বর্তমান সেটিংস দেখুন", callback_data="show_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "👋 **স্বাগতম এডমিন প্যানেলে!**\n\n"
        "⚙️ **সেটিংস পরিবর্তন করার কমান্ডসমূহ:**\n"
        "• প্রতি অ্যাডের আয় পরিবর্তন: `/set ad_reward 5`\n"
        "• মোট বিজ্ঞাপন সংখ্যা: `/set total_ads 10`\n"
        "• সর্বনিম্ন উইথড্র লিমিট: `/set min_withdraw 50`"
    )
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")

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

    elif query.data == "show_settings":
        try:
            res = requests.get(f"{DB_URL}/settings.json").json() or {}
            ad_reward = res.get("ad_reward", 1)
            total_ads = res.get("total_ads", 10)
            min_withdraw = res.get("min_withdraw", 50)
            
            msg = (
                "⚙️ **বর্তমান অ্যাপ সেটিংস:**\n\n"
                f"💰 প্রতি অ্যাডে আয়: ৳{ad_reward}\n"
                f"📺 দৈনিক মোট অ্যাড: {total_ads}টি\n"
                f"💳 সর্বনিম্ন উইথড্র: ৳{min_withdraw}"
            )
            await query.edit_message_text(msg, parse_mode="Markdown")
        except Exception:
            await query.edit_message_text("সেটিংস তথ্য আনা সম্ভব হয়নি।")

# কমান্ডের মাধ্যমে সেটিংস পরিবর্তন
async def set_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ **সঠিক ফরম্যাট:** `/set <key> <value>`\n\n"
            "উদাহরণ:\n"
            "`/set ad_reward 5` (প্রতি অ্যাডে ৫ টাকা)\n"
            "`/set total_ads 15` (মোট ১৫টি অ্যাড)\n"
            "`/set min_withdraw 100` (সর্বনিম্ন ১০০ টাকা)",
            parse_mode="Markdown"
        )
        return

    key = context.args[0]
    try:
        val = int(context.args[1])
    except ValueError:
        val = context.args[1]

    # Firebase-এ সেভ করা
    res = requests.patch(f"{DB_URL}/settings.json", json={key: val})
    if res.status_code == 200:
        await update.message.reply_text(f"✅ সফলভাবে **{key}** পরিবর্তন করে **{val}** করা হয়েছে!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ আপডেট করতে ব্যর্থ হয়েছে।")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", start))
    app.add_handler(CommandHandler("set", set_setting))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()

if __name__ == "__main__":
    main()
    
