import asyncio
import os
import requests
from datetime import datetime
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
        await update.message.reply_text("❌ Apnar ei admin panel beboharer onumoti nei.")
        return

    # --- Daily Reset Logic for Users ---
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        users_res = requests.get(f"{DB_URL}/users.json").json()
        if users_res:
            for uid, udata in users_res.items():
                if isinstance(udata, dict):
                    last_date = udata.get('last_reset_date', '')
                    if last_date != current_date:
                        requests.patch(f"{DB_URL}/users/{uid}.json", json={
                            'today_watched_ads': 0,
                            'last_reset_date': current_date
                        })
    except Exception:
        pass

    keyboard = [
        [InlineKeyboardButton("💳 Withdraw Request Check", callback_data="check_withdraw")],
        [InlineKeyboardButton("📊 Total Users", callback_data="total_users")],
        [InlineKeyboardButton("⚙️ Current Settings", callback_data="show_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "👋 *Swagotom Admin Panele!*\n\n"
        "⚙️ *Settings Poriborton Korar Commandshomuho:*\n"
        "• Proti ad-er ay poriborton: `/set ad_reward 5`\n"
        "• Motbiggapon shongkha: `/set total_ads 10`\n"
        "• Sorbonimmo withdraw limit: `/set min_withdraw 50`"
    )
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_withdraw":
        try:
            res = requests.get(f"{DB_URL}/withdrawals.json").json()
            if not res:
                await query.edit_message_text("Bortomane kono pending withdraw request nei.")
                return

            text = "📋 Pending Withdraw Talika:\n\n"
            has_pending = False
            for key, value in res.items():
                if isinstance(value, dict) and value.get("status") == "Pending":
                    has_pending = True
                    text += f"👤 Nam: {value.get('name')}\n📱 {str(value.get('method')).upper()}: {value.get('phone')}\n💰 Poriman: ৳{value.get('amount')}\n--------------------\n"
            
            if not has_pending:
                text = "Bortomane kono pending withdraw request nei."

            await query.edit_message_text(text)
        except Exception:
            await query.edit_message_text("Data load korte somoshya hoyeche.")

    elif query.data == "total_users":
        try:
            res = requests.get(f"{DB_URL}/users.json").json()
            if not res:
                await query.edit_message_text("👥 Ekhono kono registered user nei.")
                return

            text = "👥 **Registered User-der Talika:**\n\n"
            count = 1
            for uid, udata in res.items():
                if isinstance(udata, dict):
                    name = udata.get('name', 'Unknown')
                    balance = udata.get('balance', 0)
                    ads = udata.get('adsWatched', udata.get('today_watched_ads', 0))
                    text += f"{count}. **{name}**\n   🆔 ID: `{uid}`\n   💰 Balance: ৳{balance:.2f} | Ads: {ads}ti\n\n"
                    count += 1

            if len(text) > 4096:
                text = text[:4000] + "\n\n...[Talika boro tai songkhep kora holo]"

            await query.edit_message_text(text, parse_mode="Markdown")
        except Exception:
            await query.edit_message_text("User totho ana sombhob hoyni.")

    elif query.data == "show_settings":
        try:
            res = requests.get(f"{DB_URL}/settings.json").json() or {}
            ad_reward = res.get("ad_reward", 1)
            total_ads = res.get("total_ads", 10)
            min_withdraw = res.get("min_withdraw", 50)
            
            msg = (
                "⚙️ *Bortoman App Settings:*\n\n"
                f"💰 Proti ad-e ay: ৳{ad_reward}\n"
                f"📺 Dainik mot ad: {total_ads}ti\n"
                f"💳 Sorbonimmo withdraw: ৳{min_withdraw}"
            )
            await query.edit_message_text(msg, parse_mode="Markdown")
        except Exception:
            await query.edit_message_text("Settings totho ana sombhob hoyni.")

async def set_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ *Sothik Format:* `/set <key> <value>`\n\n"
            "Udahoron:\n"
            "`/set ad_reward 5`\n"
            "`/set total_ads 15`\n"
            "`/set min_withdraw 100`",
            parse_mode="Markdown"
        )
        return

    key = context.args[0]
    try:
        val = int(context.args[1])
    except ValueError:
        val = context.args[1]

    res = requests.patch(f"{DB_URL}/settings.json", json={key: val})
    if res.status_code == 200:
        await update.message.reply_text(f"✅ Shofolvabe *{key}* poriborton kore *{val}* kora hoyeche!", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Update korte byrtho hoyeche.")

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
            
