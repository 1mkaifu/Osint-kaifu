import json, imghdr, requests, datetime, csv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext
import re

# ===== CONFIG =====
BOT_TOKEN = "8234235978:AAEaivd39C5FSrTtjZeEz1JPQflOzC-Js-A"
ADMINS = [7945122206, 1363848761]  # admin IDs
COPYRIGHT = "\n\n© @IG_BANZ | All Rights Reserved"
PHOTO_URL = "https://i.ibb.co/fz8HLKpd/x.jpg"
DATA_FILE = "users.json"

# ===== USER DATA =====
try:
    with open(DATA_FILE, "r") as f:
        USERS = json.load(f)
except:
    USERS = {}

def save_users():
    with open(DATA_FILE, "w") as f:
        json.dump(USERS, f, indent=2)

def ensure_user(user_id):
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {
            "credits": 5,
            "joined_at": str(datetime.date.today()),
            "searches": 0
        }
        save_users()
    return USERS[str(user_id)]

# ===== UTILS =====
def send_with_photo(context, chat_id, text, reply_markup=None):
    if len(text) > 1024:
        caption = text[:1020] + "..."
        context.bot.send_photo(chat_id=chat_id, photo=PHOTO_URL, caption=caption, reply_markup=reply_markup)
        context.bot.send_message(chat_id=chat_id, text=text)
    else:
        context.bot.send_photo(chat_id=chat_id, photo=PHOTO_URL, caption=text, reply_markup=reply_markup)

def check_balance_and_warn(context, chat_id, u):
    if u["credits"] <= 0:
        button = InlineKeyboardMarkup([[InlineKeyboardButton("💳 Recharge Now", url="https://t.me/IG_BANZ")]])
        send_with_photo(context, chat_id, "⚠️ Your balance is 0 credits.\nPlease recharge to continue." + COPYRIGHT, reply_markup=button)
        return False
    elif u["credits"] == 1:
        send_with_photo(context, chat_id, "⚠️ Low Balance: Only 1 credit left!\nRecharge soon." + COPYRIGHT)
    return True

# ===== COMMANDS =====
def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.effective_user
    username = f"@{user.username}" if user.username else "❌ Not Set"
    first_time = False
    if str(chat_id) not in USERS:
        first_time = True
    u = ensure_user(chat_id)

    if chat_id in ADMINS:
        total_users = len(USERS)
        total_credits = sum([x["credits"] for x in USERS.values()])
        caption = (
            f"👑 Admin Panel 👑\n"
            f"Owner: @IG_BANZ\n\n"
            f"📊 Total Users: {total_users}\n"
            f"💰 Total Credits: {total_credits}\n\n"
            "⚙️ Commands:\n"
            "📱 /phone <number>\n"
            "🚗 /vehicle <RC>\n"
            "📮 /pincode <pincode>\n"
            "💳 /addcredits <id> <amt>\n"
            "💸 /subcredits <id> <amt>\n"
            "👥 /users\n"
            "📂 /exportusers\n"
            "📂 /exportjson\n"
            "📢 /broadcast <msg>"
        ) + COPYRIGHT
    else:
        caption = (
            f"🤖 OSINT Bot\n"
            f"Bot by: @IG_BANZ\n\n"
            f"💳 Balance: {u['credits']} credits\n"
            f"🗓️ Joined: {u['joined_at']}\n"
            f"🔎 Searches: {u['searches']}\n\n"
            "Commands:\n"
            "📱 /phone <number>\n"
            "🚗 /vehicle <RC>\n"
            "📮 /pincode <pincode>\n"
            "💳 /balance\n"
            "🆔 /myid"
        ) + COPYRIGHT

    send_with_photo(context, chat_id, caption)

    if first_time:
        for admin in ADMINS:
            try:
                send_with_photo(
                    context, admin,
                    f"📢 New User Joined!\n🆔 User ID: {chat_id}\n👤 Username: {username}" + COPYRIGHT
                )
            except:
                pass

# ===== CLEAN RESPONSE COMMANDS =====
def phone(update, context):
    chat_id = update.message.chat_id
    u = ensure_user(chat_id)
    if not context.args:
        send_with_photo(context, chat_id, "❌ Usage: /phone <number>" + COPYRIGHT)
        return
    if not check_balance_and_warn(context, chat_id, u): return

    number = context.args[0]
    r = requests.get(f"https://api.elitepredator.app/search_mobile?mobile={number}").json()
    u["credits"] -= 1
    u["searches"] += 1
    save_users()

    output = f"📱 Phone Info for {number}:\n\n"
    if "results" in r and isinstance(r["results"], list):
        seen = set()
        unique_results = []

        # Normalize data for duplicate removal
        def normalize(text):
            return re.sub(r'\W+', '', str(text).lower().strip())

        for res in r["results"]:
            key_tuple = (
                normalize(res.get('Name', 'N/A')),
                normalize(res.get('Father/Husband', 'N/A')),
                normalize(res.get('Address', 'N/A')),
                normalize(res.get('Mobile Number', 'N/A')),
                normalize(res.get('Alt Number', 'N/A')),
                normalize(res.get('Sim/State', 'N/A')),
                normalize(res.get('Aadhaar Card', 'N/A')),
                normalize(res.get('Email Address', 'N/A'))
            )

            if key_tuple not in seen:
                seen.add(key_tuple)
                unique_results.append(res)

        if unique_results:
            for idx, res in enumerate(unique_results, 1):
                output += f"🔍 Result {idx}:\n"
                output += f"👤 Name: {res.get('Name','N/A')}\n"
                output += f"👨‍👩‍👧 Father/Husband: {res.get('Father/Husband','N/A')}\n"
                output += f"🏠 Address: {res.get('Address','N/A')}\n"
                output += f"📞 Mobile: {res.get('Mobile Number','N/A')}\n"
                output += f"📞 Alt Number: {res.get('Alt Number','N/A')}\n"
                output += f"📡 Sim/State: {res.get('Sim/State','N/A')}\n"
                output += f"🆔 Aadhaar: {res.get('Aadhaar Card','N/A')}\n"
                output += f"📧 Email: {res.get('Email Address','N/A')}\n"
                output += "─" * 30 + "\n"
        else:
            output += "❌ No details found.\n"
    else:
        output += "❌ No details found.\n"

    output += COPYRIGHT
    send_with_photo(context, chat_id, output)

# ===== VEHICLE COMMAND =====
def vehicle(update, context):
    chat_id = update.message.chat_id
    u = ensure_user(chat_id)
    if not context.args:
        send_with_photo(context, chat_id, "❌ Usage: /vehicle <RC>" + COPYRIGHT)
        return
    if not check_balance_and_warn(context, chat_id, u): return

    rc = context.args[0]
    r = requests.get(f"https://rc-info-ng.vercel.app/?rc={rc}").json()
    u["credits"] -= 1
    u["searches"] += 1
    save_users()

    output = f"🚗 Vehicle Info for {rc}:\n\n"
    if isinstance(r, dict):
        for k, v in r.items():
            if 'owner' in k.lower():  # skip any owner field
                continue
            output += f"🔹 {k}: {v}\n"
    else:
        output += "❌ No details found.\n"

    output += COPYRIGHT
    send_with_photo(context, chat_id, output)

# ===== PINCODE COMMAND =====
def pincode(update, context):
    chat_id = update.message.chat_id
    u = ensure_user(chat_id)
    if not context.args:
        send_with_photo(context, chat_id, "❌ Usage: /pincode <pincode>" + COPYRIGHT)
        return
    if not check_balance_and_warn(context, chat_id, u): return

    code = context.args[0]
    r = requests.get(f"https://pincode-info-j4tnx.vercel.app/pincode={code}").json()
    u["credits"] -= 1
    u["searches"] += 1
    save_users()

    output = f"📮 Pincode Info {code}:\n\n"

    if isinstance(r, list) and len(r) > 0 and "PostOffice" in r[0]:
        for po in r[0]["PostOffice"]:
            for k, v in po.items():
                output += f"🔹 {k}: {v}\n"
    else:
        output += "❌ No details found.\n"

    output += COPYRIGHT
    send_with_photo(context, chat_id, output)

# ===== BALANCE / MYID =====
def balance(update, context):
    chat_id = update.message.chat_id
    u = ensure_user(chat_id)
    send_with_photo(context, chat_id, f"💳 Balance: {u['credits']} credits" + COPYRIGHT)

def myid(update, context):
    chat_id = update.message.chat_id
    send_with_photo(context, chat_id, f"🆔 Your Telegram ID: {chat_id}" + COPYRIGHT)

# ===== ADMIN COMMANDS WITH NON-ADMIN CHECK =====
def admin_required(func):
    def wrapper(update, context):
        if update.message.chat_id not in ADMINS:
            send_with_photo(context, update.message.chat_id, "Chala ja Randike Maa chod di jayegi banwau tujhe admin ka choda")
            return
        return func(update, context)
    return wrapper

@admin_required
def addcredits(update, context):
    if len(context.args) < 2: return
    uid, amt = context.args
    uid, amt = str(uid), int(amt)
    u = ensure_user(uid)
    u["credits"] += amt; save_users()
    send_with_photo(context, update.message.chat_id, f"✅ Added {amt} credits to {uid}" + COPYRIGHT)

@admin_required
def subcredits(update, context):
    if len(context.args) < 2: return
    uid, amt = context.args
    uid, amt = str(uid), int(amt)
    u = ensure_user(uid)
    u["credits"] = max(0, u["credits"] - amt); save_users()
    send_with_photo(update.message.chat_id, update.message.chat_id, f"✅ Subtracted {amt} credits from {uid}" + COPYRIGHT)

@admin_required
def users(update, context):
    text = "👥 Users:\n"
    for uid, d in USERS.items():
        text += f"{uid}: {d['credits']} credits\n"
    send_with_photo(context, update.message.chat_id, text + COPYRIGHT)

@admin_required
def exportusers(update, context):
    with open("users.csv", "w", newline="") as f:
        writer = csv.writer(f); writer.writerow(["UserID","Credits","Joined","Searches"])
        for uid,d in USERS.items():
            writer.writerow([uid,d["credits"],d["joined_at"],d["searches"]])
    context.bot.send_document(update.message.chat_id, open("users.csv","rb"))

@admin_required
def exportjson(update, context):
    context.bot.send_document(update.message.chat_id, open(DATA_FILE,"rb"))

@admin_required
def broadcast(update, context):
    msg = " ".join(context.args)
    for uid in USERS.keys():
        try:
            send_with_photo(context, int(uid), f"📢 Broadcast:\n{msg}" + COPYRIGHT)
        except: pass
    send_with_photo(context, update.message.chat_id, "✅ Broadcast sent." + COPYRIGHT)

# ===== MAIN =====
updater = Updater(BOT_TOKEN)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("phone", phone))
dp.add_handler(CommandHandler("vehicle", vehicle))
dp.add_handler(CommandHandler("pincode", pincode))
dp.add_handler(CommandHandler("balance", balance))
dp.add_handler(CommandHandler("myid", myid))
dp.add_handler(CommandHandler("addcredits", addcredits))
dp.add_handler(CommandHandler("subcredits", subcredits))
dp.add_handler(CommandHandler("users", users))
dp.add_handler(CommandHandler("exportusers", exportusers))
dp.add_handler(CommandHandler("exportjson", exportjson))
dp.add_handler(CommandHandler("broadcast", broadcast))

updater.start_polling()
updater.idle()
