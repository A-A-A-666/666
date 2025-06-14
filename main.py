# In your utils.py file

import re
import shutil  # <<< MISTAKE FIXED: Added missing import
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode # <<< MISTAKE FIXED: Added missing import
import Web
BOT_VERSION = "0.667-subdo" # <-- New version number

def escape_markdown_v2(text: str) -> str:
    # ... (this function remains the same)
    if not isinstance(text, str): text = str(text)
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

### --- NEW HELPER FUNCTIONS --- ###

def is_tool_installed(name: str) -> bool: # <<< MISTAKE FIXED: Added missing function
    """Check whether `name` is on PATH and marked as executable."""
    return shutil.which(name) is not None

async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs): # <<< MISTAKE FIXED: Added missing function
    """Sends a message, splitting it into chunks if it's too long, preserving kwargs."""
    MAX_LENGTH = 4096
    if len(text) <= MAX_LENGTH:
        await update.message.reply_text(text=text, **kwargs)
        return

    parts = []
    while len(text) > 0:
        if len(text) < MAX_LENGTH:
            parts.append(text)
            break
        
        # Find the last newline character before the limit to avoid breaking words or formatting
        split_pos = text.rfind('\n', 0, MAX_LENGTH)
        if split_pos == -1:  # No newline, have to split at the max length
            split_pos = MAX_LENGTH
            
        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip()

    # Send the first part as a reply, and subsequent parts as new messages
    is_first = True
    for part in parts:
        if part:  # Don't send empty strings
            if is_first:
                await update.message.reply_text(text=part, **kwargs)
                is_first = False
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=part, **kwargs)

### --- UPDATED BRANDING FUNCTION --- ###
def get_bot_branding():
    """Generates the bot's help message with the new /subdo command."""
    version_escaped = escape_markdown_v2(f"v{BOT_VERSION}")
    dashes = escape_markdown_v2("--------------------------------------------------")
    
    header = f"🛡️ *Doraemon Cyber Team \\- Multi\\-Tool Bot* {version_escaped} 🛡️"
    
    net_header = "*Network & Web Tools:*"
    net_tools = [
        "`/subdo <domain>` \\- Finds subdomains for a domain\\.", # ### NEW ###
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

    # Join everything together safely
    full_text = "\n".join([
        header, dashes,
        net_header, *net_tools,
        dashes,
        data_header, *data_tools
    ])
    
    return full_text
