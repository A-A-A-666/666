import re
import shutil
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

BOT_VERSION = "0.666"

def escape_markdown_v2(text: str) -> str:
    """Escapes characters for Telegram's MarkdownV2 parse mode."""
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Splits a long message into multiple messages to avoid Telegram's character limit."""
    MAX_LENGTH = 4096
    if len(text) <= MAX_LENGTH:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
        return

    parts = []
    current_part = ""
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 > MAX_LENGTH:
            parts.append(current_part)
            current_part = ""
        current_part += line + "\n"
    
    if current_part:
        parts.append(current_part)
            
    for part in parts:
        if part.strip(): # Avoid sending empty messages
            await context.bot.send_message(chat_id=update.effective_chat.id, text=part, parse_mode=ParseMode.MARKDOWN_V2)

def is_tool_installed(name: str) -> bool:
    """Check whether a command-line tool is on PATH and marked as executable."""
    return shutil.which(name) is not None

def get_bot_branding() -> str:
    """Returns the bot's help and branding message."""
    version_escaped = escape_markdown_v2(f"v{BOT_VERSION}")
    dashes = escape_markdown_v2("--------------------------------------------------")
    
    return f"""
🛡️ *Doraemon Cyber Team \- Multi\-Tool Bot* {version_escaped} 🛡️
{dashes}
*Network & Scan Tools:*
`/lookup <domain>` \- All\-in\-one WHOIS & DNS lookup\.
`/nmap <target> [opts]` \- Run an Nmap scan\.
`/rustscan <target> [opts]` \- Run a RustScan\.
`/headers <domain>` \- Get IP and HTTP headers\.
`/methods <url>` \- Find allowed HTTP methods\.
`/revip <ip>` \- Reverse IP lookup\.
{dashes}
*Web & Data Tools:*
`/analyse <url>` \- Analyse website technologies\.
`/extract <url>` \- Extract emails from a webpage\.
`/cms <url>` \- Scan a website's CMS\.
`/breach <email>` \- Check an email for breaches\.
{dashes}
*Encoding & Hashing:*
`/base64 <text>` \- Encode/Decode with buttons\.
`/md5 <text>` \- Generate MD5 hash\.
`/urlencode <text>` \- URL encode\.
`/urldecode <text>` \- URL decode\.
"""
