# In your utils.py file

import re

BOT_VERSION = "0.667-subdo" # <-- New version number

def escape_markdown_v2(text: str) -> str:
    # ... (this function remains the same)
    if not isinstance(text, str): text = str(text)
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

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
