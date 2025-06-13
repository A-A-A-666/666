import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Optional, Tuple

# Assuming you have a utils.py or helpers.py file for this function
from utils import escape_markdown_v2

logger = logging.getLogger(__name__)

def subdomain_lookup(domain: str) -> Tuple[Optional[list], Optional[str]]:
    """Scrapes a website to find subdomains."""
    url = 'https://tools.prinsh.com/home/?tools=Subdofinder'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://tools.prinsh.com',
        'Referer': url,
    }
    data = {'domain': domain}

    try:
        logger.info(f"Starting subdomain scrape for {domain}")
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator='\n')

        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        # Filter for valid-looking subdomains
        subdomains = sorted(list(set([line for line in lines if domain in line and not ' ' in line and '.' in line])))
        
        if subdomains:
            return subdomains, None
        else:
            return None, "No subdomains found. The site may have no subdomains or blocked the request."
            
    except requests.RequestException as e:
        logger.error(f"Subdomain lookup failed for {domain}: {e}")
        return None, f"An error occurred: {str(e)}"

async def subdo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /subdo command to find subdomains."""
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /subdo example.com"), parse_mode=ParseMode.MARKDOWN_V2)
        return

    domain = context.args[0].strip().lower()
    escaped_domain = escape_markdown_v2(domain)
    await update.message.reply_text(f"🔍 Searching subdomains for `{escaped_domain}`\.\.\. This can take some time\.", parse_mode=ParseMode.MARKDOWN_V2)
    
    subdomains, error = subdomain_lookup(domain)

    if error:
        await update.message.reply_text(f"⚠️ {escape_markdown_v2(error)}", parse_mode=ParseMode.MARKDOWN_V2)
        return

    if subdomains:
        header = f"🧾 *Found {len(subdomains)} subdomains for `{escaped_domain}`:*\n"
        result_text = "\n".join(subdomains)
        full_message = f"{header}```\n{result_text}\n```"

        # Handle Telegram's message length limit
        if len(full_message) > 4096:
            await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN_V2)
            # Split the text part and send in chunks
            for i in range(0, len(result_text), 4000): # Use 4000 to be safe
                chunk = result_text[i:i+4000]
                await update.message.reply_text(f"```\n{chunk}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(full_message, parse_mode=ParseMode.MARKDOWN_V2)
