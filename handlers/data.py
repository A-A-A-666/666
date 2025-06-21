# handlers/data.py

import base64
import hashlib
import urllib.parse
import json
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Optional, Tuple, Any
from utils import escape_markdown_v2, send_long_message # Added send_long_message for consistency

# --- API Configuration ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BREACH_API_URL = "https://atelegramuser.wuaze.com/email-leaked.php"
CMS_API_URL = "https://tools.prinsh.com/API/cms-scan.php"
ANALYSE_API_URL = "https://api.webtech.sh/api/v1/technologies"
EXTRACT_EMAIL_API_URL = "https://tools.prinsh.com/API/email.php"

# --- Internal Helper Functions ---
def _make_api_request(url: str, params: dict) -> Tuple[Optional[Any], Optional[str]]:
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=45)
        response.raise_for_status()
        if 'application/json' in response.headers.get('content-type', ''):
            return response.json(), None
        return response.text, None
    except requests.RequestException as e:
        return None, f"An API error occurred: {e}"

def _strip_html(text: str) -> str:
    return re.sub('<[^<]+?>', '', text)

# --- Encoding/Hashing Handlers (No changes needed here) ---

async def base64_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /base64 <text>"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    text_to_process = " ".join(context.args)
    context.user_data['b64_text'] = text_to_process
    keyboard = [[InlineKeyboardButton("🔒 Encode", callback_data="b64_encode"), InlineKeyboardButton("🔓 Decode", callback_data="b64_decode")]]
    await update.message.reply_text(
        f"Text to process:\n`{escape_markdown_v2(text_to_process)}`\n\nChoose an action:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def base64_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data
    original_text = context.user_data.get('b64_text')

    if not original_text:
        await query.edit_message_text(text=escape_markdown_v2("Error: Original text expired. Please send a new /base64 command."), parse_mode=ParseMode.MARKDOWN_V2)
        return

    if action == 'b64_encode':
        encoded_string = base64.b64encode(original_text.encode('utf-8')).decode('utf-8')
        result_text = f"*Encoded Result:*\n```\n{escape_markdown_v2(encoded_string)}\n```"
    else: # b64_decode
        try:
            decoded_string = base64.b64decode(original_text.encode('utf-8')).decode('utf-8')
            result_text = f"*Decoded Result:*\n```\n{escape_markdown_v2(decoded_string)}\n```"
        except Exception:
            result_text = escape_markdown_v2("⚠️ Error: The provided text is not valid Base64.")

    await query.edit_message_text(text=result_text, parse_mode=ParseMode.MARKDOWN_V2)
    if 'b64_text' in context.user_data:
        del context.user_data['b64_text']

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


# --- Web & Data API Handlers (Corrected) ---

async def breach_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /breach <email>"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    email, escaped_email = context.args[0], escape_markdown_v2(context.args[0])
    # **FIX APPLIED HERE**: Escaped the "..."
    await update.message.reply_text(f"🔐 Checking `{escaped_email}` for breaches{escape_markdown_v2('...')}", parse_mode=ParseMode.MARKDOWN_V2)
    api_result, error_msg = _make_api_request(BREACH_API_URL, {'email': email})

    if error_msg:
        await update.message.reply_text(f"❌ Error: {escape_markdown_v2(error_msg)}", parse_mode=ParseMode.MARKDOWN_V2)
        return
    if not api_result or not isinstance(api_result, dict):
        # **FIX APPLIED HERE**: Escaped the "."
        await update.message.reply_text(escape_markdown_v2("❓ API returned an invalid response."), parse_mode=ParseMode.MARKDOWN_V2)
        return

    breaches, pastes = api_result.get("Breaches"), api_result.get("Pastes")
    if not breaches and not pastes:
        # **FIX APPLIED HERE**: Escaped the "."
        await update.message.reply_text(f"✅ No breaches found for `{escaped_email}`.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    response_message = f"🚨 *Breach Report for `{escaped_email}`*\n"
    dashes = escape_markdown_v2("--------------------")
    if breaches:
        response_message += f"\n*Found {len(breaches)} Breach(es):*\n{dashes}\n"
        for breach in breaches:
            name = escape_markdown_v2(breach.get("Name","?"))
            domain = escape_markdown_v2(breach.get("Domain","?"))
            date = escape_markdown_v2(breach.get("BreachDate","?"))
            pwn_count = breach.get("PwnCount",0)
            description = escape_markdown_v2(_strip_html(breach.get("Description", "No description.")))
            data_classes_str = ", ".join([f"`{dc}`" for dc in breach.get("DataClasses", [])]) or "`N/A`"
            response_message += f"\n*{name}*\n  *Domain:* `{domain}`\n  *Date:* `{date}`\n  *Accounts:* `{escape_markdown_v2(f'{pwn_count:,}')}`\n  *Data:* {data_classes_str}\n  *Description:* {description}\n"

    if pastes:
        # **FIX APPLIED HERE**: Escaped the "."
        response_message += f"\n*Found {len(pastes)} Paste(s){escape_markdown_v2('.')}*\n"

    await send_long_message(update, context, response_message, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)


async def cms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /cms <url>"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    url, escaped_url = context.args[0], escape_markdown_v2(context.args[0])
    # **FIX APPLIED HERE**: Escaped the "..."
    await update.message.reply_text(f"🔍 Scanning `{escaped_url}` for CMS info{escape_markdown_v2('...')}", parse_mode=ParseMode.MARKDOWN_V2)
    api_result, error_msg = _make_api_request(CMS_API_URL, {'url': url})
    if error_msg:
        await update.message.reply_text(f"❌ Error: {escape_markdown_v2(error_msg)}", parse_mode=ParseMode.MARKDOWN_V2)
        return
    if api_result and isinstance(api_result, dict):
        response_text = f"*CMS Results for `{escaped_url}`:*\n```json\n{json.dumps(api_result, indent=2)}\n```"
        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        # **FIX APPLIED HERE**: Escaped the "."
        await update.message.reply_text(escape_markdown_v2("❓ Scan finished, but no valid results were received."), parse_mode=ParseMode.MARKDOWN_V2)


async def analyse_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /analyse <url>"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    url, escaped_url = context.args[0], escape_markdown_v2(context.args[0])
    # **FIX APPLIED HERE**: Escaped the "..."
    await update.message.reply_text(f"🔬 Analysing `{escaped_url}`{escape_markdown_v2('...')}", parse_mode=ParseMode.MARKDOWN_V2)
    api_result, error_msg = _make_api_request(ANALYSE_API_URL, {'url': url})
    if error_msg:
        await update.message.reply_text(f"❌ Analysis Error: {escape_markdown_v2(error_msg)}", parse_mode=ParseMode.MARKDOWN_V2)
        return
    if api_result and 'technologies' in api_result and api_result['technologies']:
        grouped_tech = {}
        for tech in api_result['technologies']:
            if not tech.get('categories'): continue
            category_name = tech['categories'][0]['name']
            if category_name not in grouped_tech: grouped_tech[category_name] = []
            tech_name = escape_markdown_v2(tech['name'])
            if tech.get('version'): tech_name += f" `(v{escape_markdown_v2(str(tech['version']))})`"
            grouped_tech[category_name].append(tech_name)

        response_message = f"💻 *Technology Analysis for `{escaped_url}`*\n\n"
        for category, items in sorted(grouped_tech.items()):
            response_message += f"*{escape_markdown_v2(category)}:*\n › " + ", ".join(items) + "\n\n"
        await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        # **FIX APPLIED HERE**: Escaped the "."
        await update.message.reply_text(f"❓ No specific technologies were detected for `{escaped_url}`.", parse_mode=ParseMode.MARKDOWN_V2)


async def extract_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /extract <url>"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    url, escaped_url = context.args[0], escape_markdown_v2(context.args[0])
    # **FIX APPLIED HERE**: Escaped the "..."
    await update.message.reply_text(f"📭 Extracting emails from `{escaped_url}`{escape_markdown_v2('...')}", parse_mode=ParseMode.MARKDOWN_V2)
    api_result, error_msg = _make_api_request(EXTRACT_EMAIL_API_URL, {'url': url})
    if error_msg:
        await update.message.reply_text(f"❌ Extraction Error: {escape_markdown_v2(error_msg)}", parse_mode=ParseMode.MARKDOWN_V2)
        return
    if api_result and isinstance(api_result, dict):
        if api_result.get("status") == "Good" and isinstance(api_result.get("result"), list):
            emails = api_result["result"]
            if not emails:
                response_message = f"✅ Scan complete for `{escaped_url}`. No emails found."
            else:
                email_list_str = "".join([f"{i}\\. `{escape_markdown_v2(email)}`\n" for i, email in enumerate(emails, 1)])
                response_message = f"📬 *Found {len(emails)} emails on `{escaped_url}`:*\n\n{email_list_str}"
            await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN_V2)
        elif api_result.get("status") == "Bad":
            await update.message.reply_text(f"⚠️ API Error: `{escape_markdown_v2(str(api_result.get('result')))}`", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            # **FIX APPLIED HERE**: Escaped the "."
            await update.message.reply_text(escape_markdown_v2("❓ Unexpected API response."), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        # **FIX APPLIED HERE**: Escaped the "."
        await update.message.reply_text(escape_markdown_v2("❓ Invalid API response."), parse_mode=ParseMode.MARKDOWN_V2)
