# utils.py

import re
import shutil
from telegram import Update
from telegram.ext import ContextTypes

BOT_VERSION = "0.667-subdo"

def escape_markdown_v2(text: str) -> str:
    """Escapes string for Telegram's MarkdownV2 parser."""
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def is_tool_installed(name: str) -> bool:
    """Checks whether a command-line tool is on PATH and executable."""
    return shutil.which(name) is not None

async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
    """
    Sends a message, automatically splitting it into multiple parts if it exceeds
    Telegram's character limit. Preserves kwargs for all parts.
    """
    MAX_LENGTH = 4096
    if len(text) <= MAX_LENGTH:
        await update.message.reply_text(text=text, **kwargs)
        return

    parts = []
    while len(text) > 0:
        if len(text) < MAX_LENGTH:
            parts.append(text)
            break
        
        split_pos = text.rfind('\n', 0, MAX_LENGTH)
        if split_pos == -1:
            split_pos = MAX_LENGTH
            
        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip()

    first_message_sent = False
    for part in parts:
        if part:
            if not first_message_sent:
                await update.message.reply_text(text=part, **kwargs)
                first_message_sent = True
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=part, **kwargs)

def get_bot_branding() -> str:
    """Generates the bot's help and branding message."""
    version_escaped = escape_markdown_v2(f"v{BOT_VERSION}")
    dashes = escape_markdown_v2("--------------------------------------------------")
    
    header = f"🛡️ *Doraemon Cyber Team \\- Multi\\-Tool Bot* {version_escaped} 🛡️"
    
    net_header = "*Network & Web Tools:*"
    net_tools = [
        "`/subdo <domain>` \\- Finds subdomains for a domain\\.",
        "`/lookup <domain>` \\- All\\-in\\-one WHOIS & DNS lookup\\.",
        "`/headers <domain>` \\- Gets IP and HTTP headers\\.",
        "`/methods <url>` \\- Finds allowed HTTP methods\\.",
        "`/revip <ip>` \\- Performs a reverse IP lookup\\.",
        "`/analyse <url>` \\- Analyses website technologies\\.",
        "`/extract <url>` \\- Extracts emails from a webpage\\.",
        "`/cms <url>` \\- Scans a website's CMS\\."
    ]
    
    data_header = "*Data & Security Tools:*"
    data_tools = [
        "`/breach <email>` \\- Checks an email for breaches\\.",
        "`/base64 <text>` \\- Encode/Decode with buttons\\.",
        "`/md5 <text>` \\- Generate MD5 hash\\.",
        "`/urlencode <text>` \\- URL encode\\.",
        "`/urldecode <text>` \\- URL decode\\."
    ]

    full_text = "\n".join([
        header, dashes,
        net_header, *net_tools,
        dashes,
        data_header, *data_tools
    ])
    
    return full_text
