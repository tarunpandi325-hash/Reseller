#!/usr/bin/env python3
"""Reseller Telegram Bot"""

import json
import logging
import os
import signal
import subprocess
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters,
    PicklePersistence
)
from telegram.error import Conflict, NetworkError, TimedOut

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
BOT_TOKEN        = "8571259903:AAG61wpgcY_BAwo-ZqIXeCNkhpMIMj8Jobk"
ADMIN_IDS        = [8503115617, 6761125512, 6617032248]
DATA_FILE        = "bot_data.json"
SUPPORT_CONTACTS = "@Mar1xff @Bhavisss @Pssysmglr"
CERT_BOT         = "@one_ibot"
WAITING_LOGIN    = 1
DEFAULT_CREDS    = {"user1": "pass123", "admin": "admin123"}

# ═══════════════════════════════════════════════════════════════════════════════
#  CUSTOM EMOJI  —  <tg-emoji> tags work ONLY in message text (parse_mode="HTML")
# ═══════════════════════════════════════════════════════════════════════════════
def ce(eid: str, fb: str) -> str:
    """Wrap an emoji ID in a Telegram custom-emoji HTML tag.
    fb = fallback emoji (required by Telegram API — shown to non-Premium users)."""
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

# ── Category emoji ─────────────────────────────────────────────────────────────
CE_FF    = ce("6228904568747465283", "🎮")
CE_8B    = ce("5960777057607625616", "🎱")
CE_CERT  = ce("5965079210383907241", "📜")
CE_ML    = ce("5965324474491348850", "⚔️")
CE_PUBG  = ce("6228782651805800965", "🔫")

# ── Product emoji ──────────────────────────────────────────────────────────────
CE_FLUOR   = ce("5801188682912243172", "💎")
CE_MIGUL   = ce("6233248412771295068", "⭐")
CE_DRIP    = ce("6212942266957310140", "💧")
CE_HG      = ce("6210499577322151683", "🔥")
CE_PATO    = ce("6210656322153618819", "🦆")
CE_FFH4X   = ce("6213189420850356650", "⚡")
CE_CERT2   = ce("5332823031859389246", "🏅")
CE_8BPROD  = ce("5418138833457793454", "🎱")
CE_FLUORM  = ce("5292158397465005457", "💎")

# ── UI emoji ───────────────────────────────────────────────────────────────────
CE_ACCT    = ce("5954175920506933873", "👤")
CE_CART    = ce("5440841102871517055", "🛒")
CE_DL      = ce("5298853345241358103", "📥")
CE_LOGOUT  = ce("5877341274863832725", "🚪")
CE_STATS   = ce("5877332341331857066", "📊")
CE_WALLET  = ce("5767197779155754253", "💰")
CE_ADMIN   = ce("5765087343895649564", "🔧")
CE_STATUS  = ce("6059653892025618055", "✅")
CE_AVAIL   = ce("5445195276291693508", "🟢")
CE_UNAVAIL = ce("5445102217235292298", "🔴")

# ── Category CE map ────────────────────────────────────────────────────────────
CAT_CE = {
    "ff_ios":   CE_FF,   "ff_and":   CE_FF,
    "8b_ios":   CE_8B,   "8b_and":   CE_8B,
    "cert_ios": CE_CERT,
    "ml_ios":   CE_ML,
    "pubg_ios": CE_PUBG, "pubg_and": CE_PUBG,
}

# ═══════════════════════════════════════════════════════════════════════════════
#  MENU DATA
# ═══════════════════════════════════════════════════════════════════════════════
MENU = {
    "ff_ios": {
        "label": "Free Fire (iOS)",
        "photo": "https://upload.wikimedia.org/wikipedia/en/7/76/Garena_Free_Fire_logo.png",
        "products": [
            {"name": "Fluorite",    "ce": CE_FLUOR,  "prices": [("31 Days","8.00"),("7 Days","4.00"),("1 Day","2.00")]},
            {"name": "Migul [PRO]", "ce": CE_MIGUL,  "prices": [("31 Days","6.00"),("7 Days","3.00"),("1 Day","1.00")]},
            {"name": "FFH4X",       "ce": CE_FFH4X,  "prices": [("31 Days","8.00"),("7 Days","4.00"),("1 Day","2.00")]},
            {"name": "iMAZING",     "ce": CE_FF,     "prices": [("31 Days","5.00")]},
        ],
    },
    "ff_and": {
        "label": "Free Fire (Android)",
        "photo": "https://upload.wikimedia.org/wikipedia/en/7/76/Garena_Free_Fire_logo.png",
        "products": [
            {"name": "HG-Cheats (Root)",       "ce": CE_HG,   "prices": [("31 Days","6.00"),("10 Days","3.50"),("7 Days","2.50"),("1 Day","2.00")]},
            {"name": "HG-Cheats (Non-Root)",   "ce": CE_HG,   "prices": [("31 Days","6.00"),("10 Days","4.00"),("7 Days","2.50"),("1 Day","2.00")]},
            {"name": "PatoTeam (Non-Root)",    "ce": CE_PATO, "prices": [("31 Days","6.50"),("15 Days","4.50"),("7 Days","3.00"),("1 Day","1.50")]},
            {"name": "Drip-Client (Root)",     "ce": CE_DRIP, "prices": [("31 Days","6.00"),("15 Days","4.00"),("7 Days","2.50"),("1 Day","1.00")]},
            {"name": "Drip-Client (Non-Root)", "ce": CE_DRIP, "prices": [("31 Days","6.00"),("15 Days","4.00"),("7 Days","2.50"),("1 Day","1.00")]},
        ],
    },
    "8b_ios": {
        "label": "8 Ball Pool (iOS)",
        "photo": "https://upload.wikimedia.org/wikipedia/en/8/87/8_Ball_Pool_app_logo.png",
        "products": [
            {"name": "Wizard iOS",          "ce": CE_8BPROD, "prices": [("30 Days","9.00"),("7 Days","4.00"),("1 Day","1.00")]},
            {"name": "Star Wolf GBD Pixel", "ce": CE_8BPROD, "prices": [("30 Days","5.00"),("7 Days","2.50"),("1 Day","1.00")]},
            {"name": "iOS-Viet",            "ce": CE_8BPROD, "prices": [("30 Days","10.00"),("7 Days","5.00"),("1 Day","2.00")]},
            {"name": "Potassium iOS",       "ce": CE_8BPROD, "prices": [("30 Days","7.00"),("7 Days","4.00"),("1 Day","2.00")]},
        ],
    },
    "8b_and": {
        "label": "8 Ball Pool (Android)",
        "photo": "https://upload.wikimedia.org/wikipedia/en/8/87/8_Ball_Pool_app_logo.png",
        "products": [
            {"name": "Drip 8BP",     "ce": CE_DRIP,   "prices": [("30 Days","6.00"),("7 Days","3.00"),("1 Day","1.00")]},
            {"name": "Ninja Engine", "ce": CE_8BPROD, "prices": [("30 Days","7.50"),("7 Days","4.00"),("1 Day","1.50")]},
            {"name": "Xereca 8BP",   "ce": CE_8BPROD, "prices": [("30 Days","8.00"),("7 Days","5.00"),("1 Day","2.00")]},
        ],
    },
    "cert_ios": {
        "label": "Certificate (iOS)",
        "photo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Apple_logo_grey.svg/505px-Apple_logo_grey.svg.png",
        "is_cert": True,
        "products": [
            {"name": "iPhone Certificate", "ce": CE_CERT2, "prices": [("30 Days","2.00"),("60 Days","3.50"),("90 Days","4.50"),("180 Days","6.50"),("300 Days","8.00")]},
            {"name": "iPad Certificate",   "ce": CE_CERT2, "prices": [("30 Days","2.00"),("60 Days","3.50"),("90 Days","4.50"),("180 Days","6.50"),("300 Days","8.00")]},
        ],
    },
    "ml_ios": {
        "label": "Mobile Legends (iOS)",
        "photo": "https://upload.wikimedia.org/wikipedia/en/6/64/Mobile_Legends_Bang_Bang.png",
        "products": [
            {"name": "Fluorite MLBB", "ce": CE_FLUORM, "prices": [("30 Days","8.00"),("7 Days","4.00"),("1 Day","2.00")]},
        ],
    },
    "pubg_ios": {
        "label": "PUBG Mobile (iOS)",
        "photo": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7c/Pubg_mobile_logo.png/220px-Pubg_mobile_logo.png",
        "products": [
            {"name": "Dolphin iOS",  "ce": CE_PUBG, "prices": [("30 Days","6.00"),("7 Days","3.00"),("1 Day","1.50")]},
            {"name": "Star Win iOS", "ce": CE_PUBG, "prices": [("30 Days","6.00"),("7 Days","3.00"),("1 Day","1.50")]},
            {"name": "GroX iOS",     "ce": CE_PUBG, "prices": [("30 Days","10.00"),("7 Days","6.00"),("1 Day","3.00")]},
        ],
    },
    "pubg_and": {
        "label": "PUBG Mobile (Android)",
        "photo": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7c/Pubg_mobile_logo.png/220px-Pubg_mobile_logo.png",
        "products": [
            {"name": "Zolo (Non-Root)", "ce": CE_PUBG, "prices": [("30 Days","6.00"),("7 Days","3.00"),("1 Day","1.00")]},
            {"name": "aXel PM",         "ce": CE_PUBG, "prices": [("30 Days","10.00"),("7 Days","6.00"),("1 Day","3.00")]},
            {"name": "Fluxo SRS",       "ce": CE_PUBG, "prices": [("30 Days","10.00"),("7 Days","6.00"),("1 Day","3.00")]},
        ],
    },
}
CAT_ORDER = ["ff_ios","ff_and","8b_ios","8b_and","cert_ios","ml_ios","pubg_ios","pubg_and"]


# ═══════════════════════════════════════════════════════════════════════════════
#  DATA HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def load() -> dict:
    global _MEM_DATA
    d = None
    if Path(DATA_FILE).exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            pass
    if d is None:
        # Fall back to in-memory copy if file is unreadable
        d = _MEM_DATA if _MEM_DATA else {}
    if "logged_in_users" in d and "logged_in" not in d:
        d["logged_in"] = d.pop("logged_in_users")
    elif "logged_in_users" in d:
        d.pop("logged_in_users")
    d.setdefault("logged_in", [])
    d.setdefault("files", {})
    d.setdefault("admin_ids", [])
    d.setdefault("balances", {})
    d.setdefault("credentials", dict(DEFAULT_CREDS))
    d.setdefault("_state", {})
    return d

def save(d: dict):
    global _MEM_DATA
    _MEM_DATA = d          # Always keep latest copy in memory
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)
    except PermissionError:
        try:
            os.remove(DATA_FILE)
        except Exception:
            pass
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
        except Exception:
            pass   # Data is still safe in _MEM_DATA for this session
    except Exception:
        pass       # Data is still safe in _MEM_DATA for this session

# In-memory fallback — keeps data alive when bot_data.json can't be written
_MEM_STATE: dict = {}
_MEM_DATA:  dict = {}

def get_state(d: dict, uid: int):
    key = str(uid)
    return d.get("_state", {}).get(key) or _MEM_STATE.get(key)

def set_state(d: dict, uid: int, state) -> dict:
    key = str(uid)
    _MEM_STATE[key] = state          # Always store in memory first
    d.setdefault("_state", {})[key] = state
    save(d)                          # Best-effort persist to disk
    return d

def clear_state(d: dict, uid: int) -> dict:
    key = str(uid)
    _MEM_STATE.pop(key, None)
    d.setdefault("_state", {}).pop(key, None)
    save(d)
    return d

def is_admin(uid: int, d: dict) -> bool:
    return uid in ADMIN_IDS or uid in d.get("admin_ids", [])

def is_logged(uid: int, d: dict) -> bool:
    return uid in d.get("logged_in", [])

def has_access(uid: int, d: dict) -> bool:
    return is_admin(uid, d) or is_logged(uid, d)

def get_bal(uid: int, d: dict) -> float:
    return float(d.get("balances", {}).get(str(uid), 0.0))

def set_bal(uid: int, amount: float, d: dict):
    d.setdefault("balances", {})[str(uid)] = round(max(0.0, amount), 2)

def esc(t) -> str:
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


# ═══════════════════════════════════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════════
def kb_user() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        ["Buy Keys"],
        ["Account", "Balance"],
        ["Stock",   "Log Out"],
    ], resize_keyboard=True)

def kb_admin() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        ["Buy Keys"],
        ["Account", "Balance"],
        ["Stock",   "Admin Panel"],
        ["Log Out"],
    ], resize_keyboard=True)

def kb_cats() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(MENU[k]['label'], callback_data=f"cat|{k}")]
        for k in CAT_ORDER
    ]
    return InlineKeyboardMarkup(rows)

def kb_cat(k: str) -> InlineKeyboardMarkup:
    cat = MENU[k]
    rows = [
        [InlineKeyboardButton(p["name"], callback_data=f"prod|{k}|{i}")]
        for i, p in enumerate(cat["products"])
    ]
    rows.append([InlineKeyboardButton("Back", callback_data="cats")])
    return InlineKeyboardMarkup(rows)

def kb_prod(k: str, idx: int, prod: dict) -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton("Get File",      callback_data=f"file|{k}|{idx}"),
        InlineKeyboardButton("Check Status",  callback_data=f"stat|{k}|{idx}"),
    ]]
    for dur, price in prod["prices"]:
        rows.append([InlineKeyboardButton(f"{dur}  —  ${price}", callback_data=f"buy|{k}|{idx}|{dur}|{price}")])
    rows.append([InlineKeyboardButton("Back", callback_data=f"cat|{k}")])
    return InlineKeyboardMarkup(rows)

def kb_admin_panel() -> InlineKeyboardMarkup:
    rows = []
    for k in CAT_ORDER:
        for i, p in enumerate(MENU[k]["products"]):
            rows.append([InlineKeyboardButton(f"Upload: {p['name']}", callback_data=f"up|{k}|{i}")])
    rows += [
        [InlineKeyboardButton("Add Balance",     callback_data="adm|add_bal")],
        [InlineKeyboardButton("Deduct Balance",  callback_data="adm|ded_bal")],
        [InlineKeyboardButton("Check Balance",   callback_data="adm|chk_bal")],
        [InlineKeyboardButton("Add Admin",       callback_data="adm|add_admin")],
        [InlineKeyboardButton("Add Credentials", callback_data="adm|add_creds")],
        [InlineKeyboardButton("Broadcast",       callback_data="adm|broadcast")],
        [InlineKeyboardButton("Clear All Files", callback_data="adm|clear")],
    ]
    return InlineKeyboardMarkup(rows)


# ═══════════════════════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def cat_msg(k: str) -> str:
    cat = MENU[k]
    cce = CAT_CE[k]
    lines = [f"{cce} <b>{esc(cat['label'])}</b>\n"]
    for p in cat["products"]:
        lines.append(f"{p['ce']} <b>{esc(p['name'])}</b>")
        for dur, pr in p["prices"]:
            lines.append(f"   ‣ {esc(dur)}  —  <b>${esc(pr)}</b>")
        lines.append("")
    return "\n".join(lines)

async def show_cat(msg_obj, k: str):
    cat  = MENU[k]
    text = cat_msg(k)
    kb   = kb_cat(k)
    if cat.get("photo"):
        try:
            await msg_obj.reply_photo(photo=cat["photo"], caption=text, parse_mode="HTML", reply_markup=kb)
            return
        except Exception:
            pass
    await msg_obj.reply_text(text, parse_mode="HTML", reply_markup=kb)


# ═══════════════════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d    = load()
    uid  = update.effective_user.id
    name = esc(update.effective_user.first_name or "there")
    if is_admin(uid, d):
        await update.message.reply_text(
            f"<b>Welcome back, Admin {name}!</b>\n\nReseller Bot is ready.",
            parse_mode="HTML", reply_markup=kb_admin()
        )
    elif is_logged(uid, d):
        await update.message.reply_text(
            f"<b>Welcome back, {name}!</b>\n\nTap <b>Buy Keys</b> to browse.",
            parse_mode="HTML", reply_markup=kb_user()
        )
    else:
        await update.message.reply_text(
            "<b>Welcome to the Reseller Bot!</b>\n\nUse /login to access the menu.",
            parse_mode="HTML"
        )

async def cmd_login(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d   = load()
    uid = update.effective_user.id
    if is_admin(uid, d):
        await update.message.reply_text("You are already an admin.", reply_markup=kb_admin())
        return ConversationHandler.END
    if is_logged(uid, d):
        await update.message.reply_text("Already logged in.", reply_markup=kb_user())
        return ConversationHandler.END
    await update.message.reply_text(
        "Send your credentials:\n\n<code>USERNAME\nPASSWORD</code>",
        parse_mode="HTML"
    )
    return WAITING_LOGIN

async def handle_login(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.strip().splitlines()
    if len(parts) < 2:
        await update.message.reply_text("Format:\n<code>USERNAME\nPASSWORD</code>", parse_mode="HTML")
        return WAITING_LOGIN
    user, pw = parts[0].strip(), parts[1].strip()
    d   = load()
    uid = update.effective_user.id
    if d.get("credentials", {}).get(user) == pw:
        if uid not in d["logged_in"]:
            d["logged_in"].append(uid)
        save(d)
        name = esc(update.effective_user.first_name or "User")
        await update.message.reply_text(
            f"<b>Login successful!</b>\n\nWelcome, <b>{name}</b>!\nTap <b>Buy Keys</b> to browse.",
            parse_mode="HTML", reply_markup=kb_user()
        )
        return ConversationHandler.END
    await update.message.reply_text(
        f"Wrong credentials.\n\nContact support: {SUPPORT_CONTACTS}"
    )
    return WAITING_LOGIN

async def cmd_logout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d   = load()
    uid = update.effective_user.id
    if uid in d.get("logged_in", []):
        d["logged_in"].remove(uid)
        save(d)
    await update.message.reply_text(
        f"{CE_LOGOUT} <b>Logged out.</b>\n\nUse /login to sign in again.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/login")]], resize_keyboard=True)
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>Commands</b>\n\n"
        "/start — Main menu\n"
        "/login — Log in\n"
        "/logout — Log out\n"
        "/help — This message\n\n"
        f"Support: {SUPPORT_CONTACTS}",
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  TEXT HANDLER  (button presses + admin awaiting-input states)
# ═══════════════════════════════════════════════════════════════════════════════
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d    = load()
    uid  = update.effective_user.id
    text = (update.message.text or "").strip()

    if not has_access(uid, d):
        await update.message.reply_text(
            f"<b>Access Denied.</b>\nPlease /login first.\n\nSupport: {SUPPORT_CONTACTS}",
            parse_mode="HTML"
        )
        return

    # ── Admin awaiting inputs (state stored in bot_data.json, survives restarts)
    state = get_state(d, uid)

    if state == "creds" and is_admin(uid, d):
        lines = text.splitlines()
        if len(lines) < 2:
            await update.message.reply_text("Format:\n<code>USERNAME\nPASSWORD</code>", parse_mode="HTML")
            return
        u, p = lines[0].strip(), lines[1].strip()
        d["credentials"][u] = p
        clear_state(d, uid)
        await update.message.reply_text(
            f"Credentials added.\nUser: <code>{esc(u)}</code>  Pass: <code>{esc(p)}</code>",
            parse_mode="HTML"
        )
        return

    if state == "admin_id" and is_admin(uid, d):
        try:
            new_id = int(text)
        except ValueError:
            await update.message.reply_text("Send a valid numeric Telegram User ID.")
            return
        d.setdefault("admin_ids", [])
        if new_id not in d["admin_ids"]:
            d["admin_ids"].append(new_id)
        clear_state(d, uid)
        await update.message.reply_text(f"Admin added. ID: <code>{new_id}</code>", parse_mode="HTML")
        return

    if state == "broadcast" and is_admin(uid, d):
        sent = 0
        for u_id in d.get("logged_in", []):
            try:
                await ctx.bot.send_message(chat_id=u_id, text=f"<b>Announcement</b>\n\n{esc(text)}", parse_mode="HTML")
                sent += 1
            except Exception:
                pass
        clear_state(d, uid)
        await update.message.reply_text(f"Broadcast sent to <b>{sent}</b> users.", parse_mode="HTML")
        return

    if state == "add_bal" and is_admin(uid, d):
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("Format: <code>USER_ID AMOUNT</code>", parse_mode="HTML")
            return
        try:
            tid = int(parts[0]); amt = float(parts[1])
            if amt <= 0: raise ValueError
        except ValueError:
            await update.message.reply_text("Invalid. Send: <code>USER_ID AMOUNT</code>", parse_mode="HTML")
            return
        cur = get_bal(tid, d)
        set_bal(tid, cur + amt, d)
        clear_state(d, uid)
        await update.message.reply_text(
            f"Balance updated.\nUser: <code>{tid}</code>\nAdded: <b>+${amt:.2f}</b>\nNew balance: <b>${cur+amt:.2f}</b>",
            parse_mode="HTML"
        )
        try:
            await ctx.bot.send_message(
                chat_id=tid,
                text=f"{CE_WALLET} <b>Balance Added</b>\n\n+${amt:.2f} added.\nNew balance: <b>${cur+amt:.2f}</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    if state == "ded_bal" and is_admin(uid, d):
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("Format: <code>USER_ID AMOUNT</code>", parse_mode="HTML")
            return
        try:
            tid = int(parts[0]); amt = float(parts[1])
            if amt <= 0: raise ValueError
        except ValueError:
            await update.message.reply_text("Invalid. Send: <code>USER_ID AMOUNT</code>", parse_mode="HTML")
            return
        cur = get_bal(tid, d)
        new = max(0.0, cur - amt)
        set_bal(tid, new, d)
        clear_state(d, uid)
        await update.message.reply_text(
            f"Balance updated.\nUser: <code>{tid}</code>\nDeducted: <b>-${amt:.2f}</b>\nNew balance: <b>${new:.2f}</b>",
            parse_mode="HTML"
        )
        try:
            await ctx.bot.send_message(
                chat_id=tid,
                text=f"{CE_WALLET} <b>Balance Deducted</b>\n\n-${amt:.2f} deducted.\nNew balance: <b>${new:.2f}</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    if state == "chk_bal" and is_admin(uid, d):
        try:
            tid = int(text)
        except ValueError:
            await update.message.reply_text("Send a valid numeric Telegram User ID.")
            return
        bal = get_bal(tid, d)
        clear_state(d, uid)
        await update.message.reply_text(
            f"User: <code>{tid}</code>\nBalance: <b>${bal:.2f}</b>",
            parse_mode="HTML"
        )
        return

    # ── Menu buttons ──────────────────────────────────────────────────────────
    if text == "Log Out":
        await cmd_logout(update, ctx)
        return

    if text == "Account":
        bal   = get_bal(uid, d)
        role  = "Admin" if is_admin(uid, d) else "User"
        uname = update.effective_user.username or "N/A"
        await update.message.reply_text(
            f"{CE_ACCT} <b>Account Info</b>\n\n"
            f"Name: {esc(update.effective_user.full_name or 'N/A')}\n"
            f"Username: @{esc(uname)}\n"
            f"ID: <code>{uid}</code>\n"
            f"Role: <b>{role}</b>\n"
            f"{CE_WALLET} Balance: <b>${bal:.2f}</b>\n\n"
            f"Status: Active",
            parse_mode="HTML"
        )
        return

    if text == "Balance":
        bal = get_bal(uid, d)
        await update.message.reply_text(
            f"{CE_WALLET} <b>Your Balance</b>\n\n"
            f"Available: <b>${bal:.2f}</b>\n\n"
            f"To top up, contact: {SUPPORT_CONTACTS}",
            parse_mode="HTML"
        )
        return

    if text == "Buy Keys":
        await update.message.reply_text(
            f"{CE_CART} <b>Select a category:</b>",
            parse_mode="HTML",
            reply_markup=kb_cats()
        )
        return

    if text == "Stock":
        lines = [f"{CE_STATS} <b>Stock Status</b>\n"]
        for k in CAT_ORDER:
            cat = MENU[k]
            lines.append(f"{CAT_CE[k]} <b>{esc(cat['label'])}</b>")
            for i, p in enumerate(cat["products"]):
                ok  = f"{k}_{i}" in d.get("files", {})
                dot = CE_AVAIL if ok else CE_UNAVAIL
                lines.append(f"  {dot} {p['ce']} {esc(p['name'])}")
            lines.append("")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return

    if text == "Admin Panel":
        if not is_admin(uid, d):
            await update.message.reply_text("Admins only.")
            return
        await update.message.reply_text(
            f"{CE_ADMIN} <b>Admin Panel</b>\n\nChoose an action:",
            parse_mode="HTML", reply_markup=kb_admin_panel()
        )
        return


# ═══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT HANDLER  (admin file uploads)
# ═══════════════════════════════════════════════════════════════════════════════
async def handle_doc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d   = load()
    uid = update.effective_user.id
    st  = get_state(d, uid)
    if not is_admin(uid, d) or not isinstance(st, dict) or st.get("mode") != "file":
        return
    doc = update.message.document
    if not doc:
        await update.message.reply_text("Please send a file.")
        return
    k   = st["k"]
    idx = st["idx"]
    nm  = st.get("nm", "Product")
    clear_state(d, uid)
    d.setdefault("files", {})[f"{k}_{idx}"] = doc.file_id
    save(d)
    await update.message.reply_text(
        f"File uploaded for <b>{esc(nm)}</b>.\nFile: <code>{esc(doc.file_name or 'file')}</code>",
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  CALLBACK HANDLER  (inline button presses)
# ═══════════════════════════════════════════════════════════════════════════════
async def handle_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    await q.answer()
    d   = load()
    uid = q.from_user.id
    cb  = q.data

    if not has_access(uid, d):
        await q.edit_message_text(f"Access Denied. Use /login\nSupport: {SUPPORT_CONTACTS}")
        return

    # ── Back to category list ─────────────────────────────────────────────────
    if cb == "cats":
        await q.edit_message_text(
            f"{CE_CART} <b>Select a category:</b>",
            parse_mode="HTML",
            reply_markup=kb_cats()
        )
        return

    # ── Open category ─────────────────────────────────────────────────────────
    if cb.startswith("cat|"):
        k = cb[4:]
        if k not in MENU: return
        text  = cat_msg(k)
        kb    = kb_cat(k)
        photo = MENU[k].get("photo")
        if photo:
            try:
                await q.message.reply_photo(photo=photo, caption=text, parse_mode="HTML", reply_markup=kb)
                await q.delete_message()
                return
            except Exception:
                pass
        try:
            await q.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await q.message.reply_text(text, parse_mode="HTML", reply_markup=kb)
        return

    # ── Open product ──────────────────────────────────────────────────────────
    if cb.startswith("prod|"):
        _, k, si = cb.split("|"); i = int(si)
        cat = MENU.get(k)
        if not cat or i >= len(cat["products"]): return
        p   = cat["products"][i]
        has = f"{k}_{i}" in d.get("files", {})
        await q.edit_message_text(
            f"{p['ce']} <b>{esc(p['name'])}</b>\n\n"
            f"File: {CE_AVAIL + ' Available' if has else CE_UNAVAIL + ' Not uploaded yet'}\n"
            f"{CE_STATUS} Status: Good &amp; Safe\n\n"
            f"<b>Select a duration:</b>",
            parse_mode="HTML",
            reply_markup=kb_prod(k, i, p)
        )
        return

    # ── Get file ──────────────────────────────────────────────────────────────
    if cb.startswith("file|"):
        _, k, si = cb.split("|"); i = int(si)
        cat = MENU.get(k)
        if not cat: return
        p    = cat["products"][i]
        cert = cat.get("is_cert", False)
        fid  = d.get("files", {}).get(f"{k}_{i}")
        if fid:
            caption = (
                f"{CE_DL} <b>{esc(p['name'])}</b>\n\n"
                + (f"Certificate ready!\nInstallation help: {CERT_BOT}" if cert
                   else f"Your file is ready!\nSupport: {SUPPORT_CONTACTS}")
            )
            await q.message.reply_document(document=fid, caption=caption, parse_mode="HTML")
        else:
            await q.message.reply_text(
                f"No {'certificate' if cert else 'file'} uploaded yet.\n\n"
                f"Contact: {CERT_BOT if cert else SUPPORT_CONTACTS}"
            )
        return

    # ── Check status ──────────────────────────────────────────────────────────
    if cb.startswith("stat|"):
        _, k, si = cb.split("|"); i = int(si)
        cat = MENU.get(k)
        if not cat: return
        p = cat["products"][i]
        await q.message.reply_text(
            f"{p['ce']} <b>Status — {esc(p['name'])}</b>\n\n"
            f"{CE_STATUS} Status: Good &amp; Safe\n"
            f"{CE_STATUS} Anti-ban: Active\n"
            f"{CE_STATUS} Undetected: Yes\n"
            f"{CE_STATUS} Last Checked: Today",
            parse_mode="HTML"
        )
        return

    # ── Buy / order ───────────────────────────────────────────────────────────
    if cb.startswith("buy|"):
        parts = cb.split("|")
        k, i, dur, price = parts[1], int(parts[2]), parts[3], parts[4]
        cat = MENU.get(k)
        if not cat: return
        p   = cat["products"][i]
        bal = get_bal(uid, d)
        await q.message.reply_text(
            f"{CE_CART} <b>Order Summary</b>\n\n"
            f"{p['ce']} <b>{esc(p['name'])}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\n"
            f"Price: <b>${esc(price)}</b>\n"
            f"{CE_WALLET} Your balance: <b>${bal:.2f}</b>\n\n"
            f"To complete your order, contact:\n{SUPPORT_CONTACTS}\n\n"
            f"Tell them:\n"
            f"  {esc(p['name'])} — {esc(dur)} — ${esc(price)}",
            parse_mode="HTML"
        )
        return

    # ── Admin: upload file ────────────────────────────────────────────────────
    if cb.startswith("up|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True)
            return
        _, k, si = cb.split("|"); i = int(si)
        cat = MENU.get(k)
        if not cat: return
        p = cat["products"][i]
        set_state(d, uid, {"mode": "file", "k": k, "idx": i, "nm": p["name"]})
        await q.message.reply_text(
            f"Send the file for <b>{esc(p['name'])}</b>\n\nAny format: IPA, APK, ZIP — old file will be replaced.",
            parse_mode="HTML"
        )
        return

    # ── Admin: action buttons ─────────────────────────────────────────────────
    if cb.startswith("adm|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True)
            return
        action = cb[4:]

        if action == "add_bal":
            set_state(d, uid, "add_bal")
            await q.message.reply_text(
                "<b>Add Balance</b>\n\nSend: <code>USER_ID AMOUNT</code>\n\nExample: <code>123456789 10.00</code>",
                parse_mode="HTML"
            )
        elif action == "ded_bal":
            set_state(d, uid, "ded_bal")
            await q.message.reply_text(
                "<b>Deduct Balance</b>\n\nSend: <code>USER_ID AMOUNT</code>\n\nExample: <code>123456789 5.00</code>",
                parse_mode="HTML"
            )
        elif action == "chk_bal":
            set_state(d, uid, "chk_bal")
            await q.message.reply_text("Send the Telegram User ID to check balance:")
        elif action == "add_admin":
            set_state(d, uid, "admin_id")
            await q.message.reply_text("Send the Telegram User ID of the new admin:")
        elif action == "add_creds":
            set_state(d, uid, "creds")
            await q.message.reply_text("Send new credentials:\n<code>USERNAME\nPASSWORD</code>", parse_mode="HTML")
        elif action == "broadcast":
            set_state(d, uid, "broadcast")
            await q.message.reply_text("Type your broadcast message:")
        elif action == "clear":
            await q.message.reply_text(
                "<b>Clear ALL uploaded files?</b>\nThis cannot be undone.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Yes, clear all", callback_data="adm|confirm_clear"),
                    InlineKeyboardButton("Cancel",         callback_data="adm|cancel"),
                ]])
            )
        elif action == "confirm_clear":
            d["files"] = {}
            save(d)
            await q.edit_message_text("All files cleared.")
        elif action == "cancel":
            await q.edit_message_text("Cancelled.")
        return


# ═══════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    err = ctx.error
    if isinstance(err, (Conflict, NetworkError, TimedOut)):
        logger.warning(f"Transient error (ignored): {err}")
        return
    logger.error(f"Unhandled error: {err}", exc_info=err)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    try:
        result = subprocess.run(["pgrep", "-f", "python3 bot.py"], capture_output=True, text=True)
        for pid_str in result.stdout.strip().splitlines():
            pid = int(pid_str)
            if pid != os.getpid():
                os.kill(pid, signal.SIGTERM)
    except Exception:
        pass

    # Fix permissions on data files — if locked, delete and start fresh
    for _f in [DATA_FILE, DATA_FILE + ".tmp", "bot_persistence"]:
        if not os.path.exists(_f):
            continue
        try:
            os.chmod(_f, 0o666)
        except Exception:
            pass
        # Verify we can actually write
        try:
            with open(_f, "a"):
                pass
        except PermissionError:
            try:
                os.remove(_f)
                logger.warning(f"Removed locked file {_f} — will be recreated fresh")
            except Exception:
                pass

    persistence = PicklePersistence(filepath="bot_persistence")
    app = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("login", cmd_login)],
        states={WAITING_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login)]},
        fallbacks=[CommandHandler("start", cmd_start)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("logout", cmd_logout))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CallbackQueryHandler(handle_cb))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.PRIVATE, handle_doc))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_text))
    app.add_error_handler(on_error)

    print("=" * 50)
    print("  Bot started!")
    print(f"  Admins: {ADMIN_IDS}")
    print("=" * 50)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    main()
