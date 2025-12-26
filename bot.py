import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")   # Railway env variable
ADMIN_ID = 5758431714
MAX_HISTORY = 40

# ================= COUNTRY DATABASE =================
COUNTRIES = {
    "India": ("INR", ["Asia/Kolkata"]),
    "United States": ("USD", ["America/New_York","America/Chicago","America/Los_Angeles"]),
    "United Kingdom": ("GBP", ["Europe/London"]),
    "Canada": ("CAD", ["America/Toronto","America/Vancouver"]),
    "Australia": ("AUD", ["Australia/Sydney","Australia/Perth"]),
    "UAE": ("AED", ["Asia/Dubai"]),
    "Germany": ("EUR", ["Europe/Berlin"]),
    "France": ("EUR", ["Europe/Paris"]),
    "Italy": ("EUR", ["Europe/Rome"]),
    "Spain": ("EUR", ["Europe/Madrid"]),
    "Japan": ("JPY", ["Asia/Tokyo"]),
    "South Korea": ("KRW", ["Asia/Seoul"]),
    "Brazil": ("BRL", ["America/Sao_Paulo"]),
    "Mexico": ("MXN", ["America/Mexico_City"]),
    "South Africa": ("ZAR", ["Africa/Johannesburg"]),
    "Nigeria": ("NGN", ["Africa/Lagos"]),
    "Egypt": ("EGP", ["Africa/Cairo"]),
    "Turkey": ("TRY", ["Europe/Istanbul"]),
    "Saudi Arabia": ("SAR", ["Asia/Riyadh"]),
    "Singapore": ("SGD", ["Asia/Singapore"]),
}

ALL_CURRENCIES = ["USD","INR","GBP","EUR","AED","AUD","CAD","JPY","SGD"]
ALL_TIMEZONES = [tz for _,(_,tzs) in COUNTRIES.items() for tz in tzs]

SYMBOL = {
    "USD":"$", "INR":"₹", "GBP":"£", "EUR":"€", "AED":"د.إ",
    "AUD":"A$", "CAD":"C$", "JPY":"¥", "SGD":"S$"
}

# ================= STATE =================
USER_MODE = {}
RECENT = []
SAVED = []

# ================= HELPERS =================
def is_admin(uid):
    return uid == ADMIN_ID

def low_budget(currency):
    low = {
        "USD":(3,7),"INR":(80,200),"GBP":(2,6),
        "EUR":(3,7),"AED":(10,25),
        "AUD":(4,8),"CAD":(4,8)
    }
    if random.random() < 0.8:
        a,b = low.get(currency,(3,10))
        return random.randint(a,b)
    return random.randint(10,25)

def generate_combo(mode):
    for _ in range(50):
        country = random.choice(list(COUNTRIES))
        base_cur, tzs = COUNTRIES[country]

        if mode == "strict":
            cur = base_cur
            tz = random.choice(tzs)
        elif mode == "mix":
            cur = base_cur
            tz = random.choice(ALL_TIMEZONES)
        else:
            cur = random.choice(ALL_CURRENCIES)
            tz = random.choice(ALL_TIMEZONES)

        key = (country,cur,tz)
        if key not in RECENT:
            RECENT.append(key)
            if len(RECENT) > MAX_HISTORY:
                RECENT.pop(0)
            return country,cur,tz
    return country,cur,tz

def make_plan(cur):
    daily = low_budget(cur)
    days = random.choice([1,1,1,2,3])
    return daily, days, daily*days

# ================= BOT =================
async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Access denied")
        return

    kb = [
        [InlineKeyboardButton("🎯 Generate Plan",callback_data="gen")],
        [
            InlineKeyboardButton("🔒 Strict",callback_data="m_strict"),
            InlineKeyboardButton("🔁 Mix",callback_data="m_mix"),
            InlineKeyboardButton("🎲 Random",callback_data="m_random"),
        ],
        [
            InlineKeyboardButton("⭐ Save Best",callback_data="save"),
            InlineKeyboardButton("📂 View Saved",callback_data="view"),
        ]
    ]

    await update.message.reply_text(
        "🤖 Ads Combo Bot PRO\nChoose option:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def buttons(update:Update, context:ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not is_admin(q.from_user.id):
        await q.edit_message_text("⛔ Access denied")
        return

    uid = q.from_user.id
    USER_MODE.setdefault(uid,"random")

    if q.data.startswith("m_"):
        USER_MODE[uid] = q.data.split("_")[1]
        await q.edit_message_text(f"✅ Mode set to {USER_MODE[uid].upper()}")
        return

    if q.data == "gen":
        mode = USER_MODE[uid]
        country,cur,tz = generate_combo(mode)
        daily,days,total = make_plan(cur)

        context.user_data["last"] = (country,cur,tz,daily,days,total,mode)
        s = SYMBOL.get(cur,"")

        msg = (
            "📢 Ads Budget Plan\n\n"
            f"🌍 Country: {country}\n"
            f"💱 Currency: {cur}\n"
            f"⏰ Timezone: {tz}\n\n"
            f"💵 Daily Budget: {s}{daily}\n"
            f"📆 Duration: {days} Day(s)\n"
            f"💰 Total Spend: {s}{total}\n\n"
            f"🧠 Mode: {mode.upper()}"
        )
        await q.edit_message_text(msg)
        return

    if q.data == "save":
        if "last" not in context.user_data:
            await q.edit_message_text("⚠️ Generate first")
            return
        SAVED.append(context.user_data["last"])
        await q.edit_message_text("⭐ Best plan saved")
        return

    if q.data == "view":
        if not SAVED:
            await q.edit_message_text("📂 No saved plans")
            return
        msg = "⭐ Saved Plans\n\n"
        for i,p in enumerate(SAVED[-5:],1):
            c,cu,tz,d,dy,t,m = p
            s = SYMBOL.get(cu,"")
            msg += f"{i}. {c} | {cu} | {s}{d} × {dy} = {s}{t}\n"
        await q.edit_message_text(msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.run_polling()

if __name__ == "__main__":
    main()