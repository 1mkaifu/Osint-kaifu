# -- coding: utf-8 --

import telebot, random, requests
from telebot import types

# === CONFIG ===
BOT_TOKEN = "8234235978:AAEaivd39C5FSrTtjZeEz1JPQflOzC-Js-A"
ADMIN_ID  = [7945122206, 1363848761]     # multiple admins allowed
UPI_ID    = "mohd.kaifu@sbi"

IMAGE_URL = "https://i.ibb.co/fz8HLKpd/x.jpg"
FOOTER    = "\n\n👉 𝘿𝙀𝙑𝙀𝙇𝙊𝙋 𝘽𝙔 𝙆𝘼𝙄𝙁𝙐 instagram.com/i.m.kaifu 👈"

bot = telebot.TeleBot(BOT_TOKEN)

# === STORAGE (in-memory) ===
user_credits = {}         # {user_id: credits}
username_numbers = {}     # {"@uname": "+91 ..."}
admin_state = {}          # {admin_id: {"mode": "..."}}

# === HELPERS ===
def ensure_user(uid):
    if uid not in user_credits:
        user_credits[uid] = 3  # first time 3 free credits

def rand_mobile():
    return "+91 " + str(random.randint(6345678901, 9876543210))

def calc_price(n):
    if n <= 100:
        r = 2.0
    elif n <= 1000:
        r = 1.5
    else:
        r = 1.0
    return n * r, r

def send_msg(chat_id, text, parse_mode="Markdown", reply_markup=None):
    """
    Every output = image + caption(text + footer)
    """
    caption = text + FOOTER
    bot.send_photo(chat_id, IMAGE_URL, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)

def out_of_credits(chat_id):
    msg = (
        "❌ Credits Khatam!\n\n"
        "💳 Rate Chart\n\n"
        "• 1–100 = ₹2/credit\n"
        "• 101–1000 = ₹1.5/credit\n"
        "• 1001+ = ₹1/credit\n\n"
        f"📲 Pay via UPI: `{UPI_ID}`\n"
        "👉 /buy ya /buy 150 likhkar price dekho."
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Buy Credits", callback_data="rates"))
    kb.add(types.InlineKeyboardButton("📩 Contact Admin", url=f"tg://user?id={ADMIN_ID[0]}"))
    send_msg(chat_id, msg, parse_mode="Markdown", reply_markup=kb)

def safe_json(resp):
    """
    Try JSON; if fail, return None
    """
    try:
        return resp.json()
    except:
        return None

def format_kv_lines(data: dict, mapping: list):
    """
    mapping: [(key_in_data, label_with_emoji)]
    """
    lines = []
    for key, label in mapping:
        val = data.get(key, "N/A")
        if val is None or val == "":
            val = "N/A"
        lines.append(f"{label} <b>{val}</b>")
    return "\n".join(lines)

def format_plain_text(text: str):
    """
    Split plain text (one-line) into neat lines.
    Tries common separators, else whitespace.
    """
    t = text.strip()
    if not t:
        return "N/A"
    seps = [", ", "|", ";", ","]  # common separators
    for s in seps:
        if s in t:
            parts = [p.strip() for p in t.split(s) if p.strip()]
            return "\n".join(f"➡️ {p}" for p in parts)
    # fallback: whitespace chunks (limit length)
    parts = t.split()
    # group in sensible chunks
    return "\n".join(f"➡️ {p}" for p in parts)

# === START + BASICS ===
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    ensure_user(uid)

    txt = (
        f"👋 Welcome {m.from_user.first_name or ''}!\n\n"
        "🎁 Pehli baar 3 Free Credits mil gaye.\n\n"
        "Commands:\n"
        "• /username @username – random number demo\n"
        "• /pincode <code> – area info\n"
        "• /vehicle <RC> – vehicle info\n"
        "• /number <mobile> – number info\n"
        "• /credits – apne credits\n"
        "• /buy  or  /buycredits – rate & price\n"
        "• /myid – apna Telegram ID\n"
        "• /about – bot info\n"
        "• /admin – admin/help"
    )
    send_msg(m.chat.id, txt)

@bot.message_handler(commands=['myid'])
def myid(m):
    send_msg(m.chat.id, f"🆔 {m.from_user.id}", parse_mode="Markdown")

@bot.message_handler(commands=['credits'])
def credits(m):
    ensure_user(m.from_user.id)
    send_msg(m.chat.id, f"💳 Aapke paas {user_credits[m.from_user.id]} credits hain.")

@bot.message_handler(commands=['about'])
def about_cmd(m):
    txt = (
        "🤖 *About This Bot*\n\n"
        "🔹 Username → Mobile (demo)\n"
        "🔹 Pincode info → /pincode 110062\n"
        "🔹 Vehicle info → /vehicle MH01AB1234\n"
        "🔹 Number info → /number 9876543210\n\n"
        "💳 Credit system enabled\n"
        "👨‍💻 Admin panel available"
    )
    send_msg(m.chat.id, txt, parse_mode="Markdown")

# === BUY / RATES ===
@bot.message_handler(commands=['buy','buycredit','buycredits'])
def buy(m):
    msg = (
        "💳 *Credit Rate Chart*\n\n"
        "• 1–100 = ₹2/credit\n"
        "• 101–1000 = ₹1.5/credit\n"
        "• 1001+ = ₹1/credit\n\n"
        "🧮 Example:\n"
        "/buy 50  → ₹100\n"
        "/buy 150 → ₹225\n"
        "/buy 1200 → ₹1200\n\n"
        f"📲 Pay via UPI: `{UPI_ID}`\n"
        "Payment ke baad /myid bhejein."
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📩 Contact Admin", url=f"tg://user?id={ADMIN_ID[0]}"))
    send_msg(m.chat.id, msg, parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("/buy ") and len(m.text.split())==2 and m.text.split()[1].isdigit())
def buy_calc(m):
    n = int(m.text.split()[1])
    if n <= 0:
        send_msg(m.chat.id, "⚠️ Credits 1 se zyada honi chahiye.")
        return
    price, rate = calc_price(n)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📩 Contact Admin", url=f"tg://user?id={ADMIN_ID[0]}"))
    price_str = f"{int(price) if float(price).is_integer() else price:.2f}"
    send_msg(
        m.chat.id,
        f"🛒 Purchase Summary\n\nCredits: {n}\nRate: ₹{rate}/credit\nPrice: ₹{price_str}\n\n"
        f"📲 UPI: `{UPI_ID}`\nPayment ke baad /myid bhejein.",
        parse_mode="Markdown",
        reply_markup=kb
    )

# === USERNAME LOOKUP (demo same as original random) ===
@bot.message_handler(commands=['username'])
def username_cmd(m):
    ensure_user(m.from_user.id)
    if user_credits[m.from_user.id] <= 0:
        out_of_credits(m.chat.id); return
    parts = m.text.split(maxsplit=1)
    if len(parts) == 1:
        send_msg(m.chat.id, "👉 Konsa username? @username bhejo."); return
    _handle_username(m, parts[1].strip())

@bot.message_handler(func=lambda m: m.text and m.text.strip().startswith("@"))
def any_at(m):
    ensure_user(m.from_user.id)
    if user_credits[m.from_user.id] <= 0:
        out_of_credits(m.chat.id); return
    _handle_username(m, m.text.strip())

def _handle_username(m, uname):
    u = uname.lower()
    if u in username_numbers:
        num = username_numbers[u]
    else:
        num = rand_mobile()
        username_numbers[u] = num

    user_credits[m.from_user.id] -= 1
    send_msg(
        m.chat.id,
        f"✅ Username Search Result\n\n🔗 Username: {u}\n📱 Mobile: {num}\n\n"
        f"💳 Remaining Credits: {user_credits[m.from_user.id]}"
    )
    if user_credits[m.from_user.id] == 0:
        out_of_credits(m.chat.id)

# === PINCODE (formatted, JSON or plain) ===
@bot.message_handler(commands=['pincode'])
def pincode_cmd(m):
    ensure_user(m.from_user.id)
    if user_credits[m.from_user.id] <= 0:
        out_of_credits(m.chat.id); return
    parts = m.text.split(maxsplit=1)
    if len(parts) == 1:
        send_msg(m.chat.id, "👉 Example: /pincode 110062"); return
    code = parts[1].strip()
    try:
        r = requests.get(f"https://pincode-info-j4tnx.vercel.app/pincode={code}", timeout=10)
        data = safe_json(r)
        if isinstance(data, dict):
            msg = format_kv_lines(data, [
                ("pincode","📍 Pincode:"),
                ("area","🏘 Area:"),
                ("district","🏢 District:"),
                ("state","🌍 State:"),
                ("po","📮 Post Office:"),
                ("circle","🔑 Circle:")
            ])
        else:
            msg = format_plain_text(r.text)
        send_msg(m.chat.id, f"🔎 Pincode {code} info:\n\n{msg}", parse_mode="HTML")
    except Exception as e:
        send_msg(m.chat.id, f"❌ API Error ya galat pincode.\n\n`{e}`", parse_mode="Markdown")

# === VEHICLE (formatted, JSON or plain) ===
@bot.message_handler(commands=['vehicle'])
def vehicle_cmd(m):
    ensure_user(m.from_user.id)
    if user_credits[m.from_user.id] <= 0:
        out_of_credits(m.chat.id); return
    parts = m.text.split(maxsplit=1)
    if len(parts) == 1:
        send_msg(m.chat.id, "👉 Example: /vehicle MH01AB1234"); return
    rc = parts[1].strip().upper()
    try:
        r = requests.get(f"https://rc-info-ng.vercel.app/?rc={rc}", timeout=10)
        data = safe_json(r)
        if isinstance(data, dict):
            msg = format_kv_lines(data, [
                ("vehicle_no","🚗 Vehicle No:"),
                ("model","🏍 Model:"),
                ("rto","🏢 RTO:"),
                ("owner","👤 Owner:"),
                ("reg_date","📅 Registration Date:"),
                ("engine_no","🛠 Engine No:"),
                ("chassis_no","🔑 Chassis No:"),
                ("fuel","💡 Fuel Type:")
            ])
        else:
            msg = format_plain_text(r.text)
        user_credits[m.from_user.id] -= 1
        send_msg(m.chat.id, f"🔎 Vehicle {rc} info:\n\n{msg}", parse_mode="HTML")
        if user_credits[m.from_user.id] == 0:
            out_of_credits(m.chat.id)
    except Exception as e:
        send_msg(m.chat.id, f"❌ API Error ya galat RC number.\n\n`{e}`", parse_mode="Markdown")

# === NUMBER (formatted, JSON or plain) ===
@bot.message_handler(commands=['number'])
def number_cmd(m):
    ensure_user(m.from_user.id)
    if user_credits[m.from_user.id] <= 0:
        out_of_credits(m.chat.id); return
    parts = m.text.split(maxsplit=1)
    if len(parts) == 1:
        send_msg(m.chat.id, "👉 Example: /number 7078991721"); return
    num = parts[1].strip()
    try:
        r = requests.get(f"https://api.elitepredator.app/search_mobile?mobile={num}", timeout=15)
        data = safe_json(r)
        if isinstance(data, dict):
            msg = format_kv_lines(data, [
                ("mobile","📞 Mobile:"),
                ("name","👤 Name:"),
                ("fname","👨‍👩‍👦 Father Name:"),
                ("address","🏠 Address:"),
                ("alt","📲 Alternate:"),
                ("circle","🌍 Circle:"),
                ("email","✉️ Email:")
            ])
        else:
            msg = format_plain_text(r.text)
        user_credits[m.from_user.id] -= 1
        send_msg(m.chat.id, f"🔎 Number {num} info:\n\n{msg}", parse_mode="HTML")
        if user_credits[m.from_user.id] == 0:
            out_of_credits(m.chat.id)
    except Exception as e:
        send_msg(m.chat.id, f"❌ API Error ya galat number.\n\n`{e}`", parse_mode="Markdown")

# === ADMIN PANEL (as you had) ===
@bot.message_handler(commands=['admin'])
def admin(m):
    if m.from_user.id not in ADMIN_ID:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("👨‍💻 Contact Admin", url=f"tg://user?id={ADMIN_ID[0]}"))
        send_msg(m.chat.id, "📩 Help/recharge ke liye admin se contact karein.", reply_markup=kb)
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("👥 Users List", callback_data="users_list"))
    kb.add(types.InlineKeyboardButton("📂 Users Count", callback_data="users_count"))
    kb.add(types.InlineKeyboardButton("📈 Rate Chart",  callback_data="rates"))
    kb.add(types.InlineKeyboardButton("➕ Add Credits", callback_data="adm_add"))
    kb.add(types.InlineKeyboardButton("➖ Remove Credits", callback_data="adm_remove"))
    kb.add(types.InlineKeyboardButton("🧰 Set Credits", callback_data="adm_set"))
    kb.add(types.InlineKeyboardButton("🔎 Check Credits", callback_data="adm_check"))
    send_msg(m.chat.id, "⚙️ *Admin Panel*", parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("adm") or c.data in {"users_list","users_count","rates"}:
        if c.from_user.id not in ADMIN_ID:
            return

    if c.data == "users_list":
        if not user_credits:
            send_msg(c.message.chat.id, "📂 Koi user nahi.")
        else:
            lines = ["👥 *Users List*\n"]
            for uid, cr in user_credits.items():
                lines.append(f"• {uid} → {cr} credits")
            send_msg(c.message.chat.id, "\n".join(lines), parse_mode="Markdown")

    elif c.data == "users_count":
        send_msg(c.message.chat.id, f"📂 *Total Users:* {len(user_credits)}", parse_mode="Markdown")

    elif c.data == "rates":
        msg = (
            "💳 *Credit Rate Chart*\n\n"
            "• 1–100 = ₹2/credit\n"
            "• 101–1000 = ₹1.5/credit\n"
            "• 1001+ = ₹1/credit\n\n"
            f"📲 UPI: `{UPI_ID}`\nExample: `/buy 350`"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📩 Contact Admin", url=f"tg://user?id={ADMIN_ID[0]}"))
        send_msg(c.message.chat.id, msg, parse_mode="Markdown", reply_markup=kb)

    elif c.data == "adm_add":
        admin_state[c.from_user.id] = {"mode": "add"}
        send_msg(c.message.chat.id, "➕ Send: `user_id amount`", parse_mode="Markdown")
    elif c.data == "adm_remove":
        admin_state[c.from_user.id] = {"mode": "remove"}
        send_msg(c.message.chat.id, "➖ Send: `user_id amount`", parse_mode="Markdown")
    elif c.data == "adm_set":
        admin_state[c.from_user.id] = {"mode": "set"}
        send_msg(c.message.chat.id, "🧰 Send: `user_id amount`", parse_mode="Markdown")
    elif c.data == "adm_check":
        admin_state[c.from_user.id] = {"mode": "check"}
        send_msg(c.message.chat.id, "🔎 Send: `user_id`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: (m.from_user.id in ADMIN_ID) and (m.from_user.id in admin_state))
def admin_input(m):
    mode = admin_state[m.from_user.id]["mode"]
    try:
        if mode in {"add","remove","set"}:
            parts = m.text.split()
            uid, amt = int(parts[0]), int(parts[1])
            ensure_user(uid)
            if mode == "add":
                user_credits[uid] += amt
                send_msg(m.chat.id, f"✅ {uid} +{amt} → {user_credits[uid]}")
                send_msg(uid, f"🎁 Admin ne +{amt} credits diye! Total: {user_credits[uid]}")
            elif mode == "remove":
                user_credits[uid] = max(0, user_credits[uid] - amt)
                send_msg(m.chat.id, f"🗑 {uid} -{amt} → {user_credits[uid]}")
                send_msg(uid, f"⚠️ Admin ne {amt} credits remove kiye. Bache: {user_credits[uid]}")
            else:  # set
                user_credits[uid] = max(0, amt)
                send_msg(m.chat.id, f"🧰 {uid} set → {user_credits[uid]}")
                send_msg(uid, f"ℹ️ Admin ne aapke credits set kiye: {user_credits[uid]}")
        elif mode == "check":
            uid = int(m.text.strip())
            send_msg(m.chat.id, f"🆔 {uid} → {user_credits.get(uid,0)} credits")
    except:
        send_msg(m.chat.id, "❌ Galat format. Example: `8171444846 100`", parse_mode="Markdown")
    finally:
        admin_state.pop(m.from_user.id, None)

# === RUN ===
print("🤖 Bot is running…")
bot.infinity_polling()
