import base64
import hashlib
import urllib.parse
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from utils import escape_markdown_v2

# --- API Configuration ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BREACH_API_URL = "https://atelegramuser.wuaze.com/email-leaked.php"
CMS_API_URL = "https://tools.prinsh.com/API/cms-scan.php"
ANALYSE_API_URL = "https://api.webtech.sh/api/v1/technologies"
EXTRACT_EMAIL_API_URL = "https://tools.prinsh.com/API/email.php"

# --- Base64 with Buttons ---
async def base64_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /base64 <your text here>"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    text_to_process = " ".join(context.args)
    context.user_data['b64_text'] = text_to_process

    keyboard = [[
        InlineKeyboardButton("🔒 Encode", callback_data="b64_encode"),
        InlineKeyboardButton("🔓 Decode", callback_data="b64_decode"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Text to process:\n`{escape_markdown_v2(text_to_process)}`\n\nChoose an action:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def base64_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data
    original_text = context.user_data.get('b64_text')

    if not original_text:
        await query.edit_message_text(text=escape_markdown_v2("Error: Original text expired."), parse_mode=ParseMode.MARKDOWN_V2)
        return

    result_text = ""
    if action == 'b64_encode':
        encoded_string = base64.b64encode(original_text.encode('utf-8')).decode('utf-8')
        result_text = f"*Encoded Result:*\n```\n{escape_markdown_v2(encoded_string)}\n```"
    elif action == 'b64_decode':
        try:
            decoded_string = base64.b64decode(original_text.encode('utf-8')).decode('utf-8')
            result_text = f"*Decoded Result:*\n```\n{escape_markdown_v2(decoded_string)}\n```"
        except Exception:
            result_text = escape_markdown_v2("⚠️ Error: The provided text is not valid Base64.")
            
    await query.edit_message_text(text=result_text, parse_mode=ParseMode.MARKDOWN_V2)
    if 'b64_text' in context.user_data:
        del context.user_data['b64_text']

# --- Other Data Handlers ---
async def md5_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("Usage: `/md5 <text>`", parse_mode=ParseMode.MARKDOWN_V2); return
    text_to_hash = " ".join(context.args)
    hashed_text = hashlib.md5(text_to_hash.encode('utf-8')).hexdigest()
    await update.message.reply_text(f"*MD5 Hash:*\n```\n{hashed_text}\n```", parse_mode=ParseMode.MARKDOWN_V2)

async def urlencode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("Usage: `/urlencode <text>`", parse_mode=ParseMode.MARKDOWN_V2); return
    text_to_encode = " ".join(context.args)
    encoded_string = urllib.parse.quote(text_to_encode)
    await update.message.reply_text(f"*URL Encoded:*\n```\n{encoded_string}\n```", parse_mode=ParseMode.MARKDOWN_V2)

async def urldecode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("Usage: `/urldecode <text>`", parse_mode=ParseMode.MARKDOWN_V2); return
    text_to_decode = " ".join(context.args)
    decoded_string = urllib.parse.unquote(text_to_decode)
    await update.message.reply_text(f"*URL Decoded:*\n```\n{escape_markdown_v2(decoded_string)}\n```", parse_mode=ParseMode.MARKDOWN_V2)

# --- Breach Command (from previous version) ---
async def breach_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # This command uses the detailed logic from our previous conversation.
    # It has been omitted here for brevity but should be pasted in from the
    # last version (3.0-TG-BreachDetail) where we fixed it.
    await update.message.reply_text("Breach command logic goes here...")
    
# --- Other API-based commands (CMS, Analyse, Extract) ---
# These would also be included here, calling the relevant APIs.
async def cms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("CMS command logic goes here...")

async def analyse_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Analyse command logic goes here...")

async def extract_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Extract command logic goes here...")
