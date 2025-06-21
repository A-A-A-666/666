# handlers/subdomain_finder.py

import logging
import requests
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Optional, Tuple, Set

from utils import escape_markdown_v2, send_long_message

logger = logging.getLogger(__name__)

def find_subdomains_crtsh(domain: str) -> Tuple[Optional[list], Optional[str]]:
    """
    Finds subdomains by querying the crt.sh Certificate Transparency log search.
    """
    logger.info(f"Starting crt.sh subdomain lookup for {domain}")
    subdomains: Set[str] = set()
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=45)
        response.raise_for_status()

        if not response.text:
            return None, "No subdomains found. The certificate log may be empty for this domain."
            
        json_data = response.json()
        if not json_data:
            return None, "No subdomains found. The certificate log may be empty for this domain."

        for entry in json_data:
            names = entry.get('name_value', '').split('\n')
            for name in names:
                clean_name = name.strip()
                if clean_name and not clean_name.startswith('*.'):
                    subdomains.add(clean_name)
        
        if subdomains:
            return sorted(list(subdomains)), None
        else:
            return None, "No subdomains found after parsing the certificate logs."

    except requests.RequestException as e:
        logger.error(f"crt.sh lookup failed for {domain}: {e}")
        return None, f"An API error occurred: {str(e)}"
    except ValueError:
        logger.error(f"Failed to decode JSON from crt.sh for domain {domain}")
        return None, "The API returned an invalid (non-JSON) response. It may be temporarily unavailable."

async def subdo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /subdo command to find subdomains using crt.sh."""
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /subdo example.com"), parse_mode=ParseMode.MARKDOWN_V2)
        return

    domain = context.args[0].strip().lower()
    escaped_domain = escape_markdown_v2(domain)
    # **FIX APPLIED HERE**: Escaped the "..." and "."
    await update.message.reply_text(f"🔍 Searching certificate logs for `{escaped_domain}`{escape_markdown_v2('...')} This can take some time{escape_markdown_v2('.')}", parse_mode=ParseMode.MARKDOWN_V2)
    
    subdomains, error = find_subdomains_crtsh(domain)

    if error:
        await update.message.reply_text(f"⚠️ {escape_markdown_v2(error)}", parse_mode=ParseMode.MARKDOWN_V2)
        return

    if subdomains:
        header = f"🧾 *Found {len(subdomains)} subdomains for `{escaped_domain}` via crt\\.sh:*\n"
        # Text inside a ``` code block does NOT need to be escaped.
        result_text = "\n".join(subdomains)
        full_message = f"{header}```\n{result_text}\n```"
        
        await send_long_message(update, context, full_message, parse_mode=ParseMode.MARKDOWN_V2)
