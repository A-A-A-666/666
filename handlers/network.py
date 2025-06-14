import whois
import dns.resolver
import subprocess
import re
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode  # <<< MISTAKE FIXED
from typing import Optional, Tuple, Any, Dict
from utils import escape_markdown_v2, send_long_message, is_tool_installed

# --- Config ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REV_IP_API_URL = "https://tools.prinsh.com/API/revip.php"

# --- Internal Helper for /headers ---
def _get_header_data(domain: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Gathers DNS and HTTP header info for a domain."""
    try:
        ipv4 = [ip.to_text() for ip in dns.resolver.resolve(domain, 'A')]
        ipv6 = []
        try: ipv6 = [ip.to_text() for ip in dns.resolver.resolve(domain, 'AAAA')]
        except (dns.resolver.NoAnswer, dns.resolver.NoNameservers): pass
        headers = {}
        try:
            response = requests.get(f"https://{domain}", timeout=10, headers={'User-Agent': USER_AGENT}, allow_redirects=True)
            headers = response.headers
        except requests.RequestException:
            try:
                response = requests.get(f"http://{domain}", timeout=10, headers={'User-Agent': USER_AGENT}, allow_redirects=True)
                headers = response.headers
            except requests.RequestException: pass
        return {"domain": domain, "ipv4": ipv4, "ipv6": ipv6, "headers": dict(headers)}, None
    except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.resolver.Timeout) as e:
        return None, f"Could not resolve domain: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

# --- Command Handlers ---

async def nmap_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_tool_installed('nmap'):
        await update.message.reply_text(escape_markdown_v2("⚠️ Nmap is not installed. Admin: please run `sudo apt-get install nmap`."), parse_mode=ParseMode.MARKDOWN_V2)
        return
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /nmap <target> [opts]\nExample: /nmap example.com -F -sV"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    target = context.args[0]
    if not re.match(r"^[a-zA-Z0-9.-]+$", target):
        await update.message.reply_text(escape_markdown_v2("⚠️ Invalid target format. Only IPs and hostnames allowed."), parse_mode=ParseMode.MARKDOWN_V2)
        return
    allowed_flags = ['-F', '-sV', '-sC', '-T4', '-p-', '-Pn', '-A', '-O', '-v']
    user_flags = context.args[1:]
    if any(flag not in allowed_flags for flag in user_flags):
        await update.message.reply_text(escape_markdown_v2(f"⚠️ Disallowed flag detected. Allowed: {', '.join(allowed_flags)}"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    await update.message.reply_text(f"Starting Nmap scan on `{escape_markdown_v2(target)}`\.\.\. This can take up to 5 minutes.", parse_mode=ParseMode.MARKDOWN_V2)
    command = ['nmap'] + user_flags + [target]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        output = result.stdout or result.stderr or "Scan completed with no output."
        response_text = f"*Nmap Scan Results for `{escape_markdown_v2(target)}`*\n\n```\n{escape_markdown_v2(output)}\n```"
        # <<< MISTAKE FIXED: Added parse_mode argument
        await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2)
    except subprocess.TimeoutExpired:
        await update.message.reply_text(escape_markdown_v2(f"❌ Scan timed out after 5 minutes for target: {target}"), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await update.message.reply_text(escape_markdown_v2(f"❌ Nmap scan error: {str(e)}"), parse_mode=ParseMode.MARKDOWN_V2)

async def rustscan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_tool_installed('rustscan'):
        await update.message.reply_text(escape_markdown_v2("⚠️ RustScan is not installed. Admin: please install it from GitHub."), parse_mode=ParseMode.MARKDOWN_V2)
        return
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /rustscan <target>"), parse_mode=ParseMode.MARKDOWN_V2)
        return
    target = context.args[0]
    if not re.match(r"^[a-zA-Z0-9.-]+$", target):
        await update.message.reply_text(escape_markdown_v2("⚠️ Invalid target format."), parse_mode=ParseMode.MARKDOWN_V2)
        return
    await update.message.reply_text(f"Starting RustScan on `{escape_markdown_v2(target)}`\.\.\. This can take a moment.", parse_mode=ParseMode.MARKDOWN_V2)
    command = ['rustscan', '-a', target, '--', '-sV'] # Basic scan with service version
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        output = result.stdout or result.stderr or "Scan completed with no output."
        # Clean up RustScan's overly verbose output
        cleaned_output = "\n".join([line for line in output.split('\n') if 'Starting Nmap' not in line and 'METADATA' not in line])
        response_text = f"*RustScan Results for `{escape_markdown_v2(target)}`*\n\n```\n{escape_markdown_v2(cleaned_output)}\n```"
        # <<< MISTAKE FIXED: Added parse_mode argument
        await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2)
    except subprocess.TimeoutExpired:
        await update.message.reply_text(escape_markdown_v2(f"❌ Scan timed out after 5 minutes for target: {target}"), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await update.message.reply_text(escape_markdown_v2(f"❌ RustScan error: {str(e)}"), parse_mode=ParseMode.MARKDOWN_V2)

async def lookup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text(escape_markdown_v2("Usage: /lookup <domain>"), parse_mode=ParseMode.MARKDOWN_V2); return
    domain = context.args[0].lower().strip().replace("http://", "").replace("https://", "")
    escaped_domain = escape_markdown_v2(domain)
    await update.message.reply_text(f"🕵️ Digging deep into `{escaped_domain}`\.\.\.", parse_mode=ParseMode.MARKDOWN_V2)
    response_text = f"🔎 *Lookup Report for `{escaped_domain}`*\n" + escape_markdown_v2("----------------------------------------\n\n")
    try:
        w = whois.whois(domain)
        response_text += "*WHOIS Information:*\n"
        if w.text and w.domain_name:
             for key, value in w.items():
                if value and key != 'text':
                    value_str = ", ".join(map(str, value)) if isinstance(value, list) else (value.strftime('%Y-%m-%d %H:%M:%S') if isinstance(value, datetime) else str(value))
                    key_str = ' '.join(word.capitalize() for word in key.split('_'))
                    response_text += f"  *{escape_markdown_v2(key_str)}:* `{escape_markdown_v2(value_str)}`\n"
        else:
            response_text += "  `No public WHOIS data found.`\n"
        response_text += "\n"
    except Exception as e:
        response_text += f"*WHOIS Information:*\n  `Error: {escape_markdown_v2(str(e))}`\n\n"
    response_text += "*DNS Records:*\n"
    for r_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']:
        try:
            answers = dns.resolver.resolve(domain, r_type)
            records = [str(r).strip() for r in answers]
            if records:
                response_text += f"  *{escape_markdown_v2(r_type)}:*\n"
                for record in records: response_text += f"    `{escape_markdown_v2(record)}`\n"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
            pass
        except Exception: pass
    # <<< MISTAKE FIXED: Added parse_mode argument
    await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2)

async def headers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text(escape_markdown_v2("Usage: /headers <domain>"), parse_mode=ParseMode.MARKDOWN_V2); return
    domain = context.args[0].replace("http://", "").replace("https://", "").split("/")[0]
    escaped_domain = escape_markdown_v2(domain)
    await update.message.reply_text(f"📡 Getting headers for `{escaped_domain}`...", parse_mode=ParseMode.MARKDOWN_V2)
    data, error = _get_header_data(domain)
    if error: await update.message.reply_text(f"❌ Error: {escape_markdown_v2(error)}", parse_mode=ParseMode.MARKDOWN_V2); return
    if data:
        response_text = f"🌐 *Info for `{escaped_domain}`*\n"
        if data.get('ipv4'): response_text += f"\n*IPv4:* `{', '.join(data['ipv4'])}`"
        if data.get('ipv6'): response_text += f"\n*IPv6:* `{', '.join(data['ipv6'])}`"
        if data.get('headers'):
            headers_str = "\n\n*HTTP Headers:*\n"
            for key, val in data['headers'].items(): headers_str += f"*{escape_markdown_v2(key)}:* `{escape_markdown_v2(val)}`\n"
            if len(response_text + headers_str) > 4000: response_text += "\n\n_Headers too long to display._"
            else: response_text += headers_str
        else: response_text += "\n\n_Could not retrieve HTTP headers._"
        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)

async def methods_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text(escape_markdown_v2("Usage: /methods <url>"), parse_mode=ParseMode.MARKDOWN_V2); return
    url = context.args[0]
    if not url.startswith(('http://', 'https://')): url = 'http://' + url
    escaped_url = escape_markdown_v2(url)
    await update.message.reply_text(f"🔎 Checking methods for `{escaped_url}`...", parse_mode=ParseMode.MARKDOWN_V2)
    try:
        response = requests.options(url, timeout=10, headers={'User-Agent': USER_AGENT})
        allowed_methods = response.headers.get('Allow', 'Not specified')
        response_text = f"📋 *Allowed Methods for `{escaped_url}`*\n`{escape_markdown_v2(allowed_methods)}`\n_(Status: {response.status_code})_"
    except requests.RequestException as e:
        response_text = f"❌ Could not connect to `{escaped_url}`.\n*Error:* `{escape_markdown_v2(str(e))}`"
    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)

async def revip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text(escape_markdown_v2("Usage: /revip <ip>"), parse_mode=ParseMode.MARKDOWN_V2); return
    ip, escaped_ip = context.args[0], escape_markdown_v2(context.args[0])
    await update.message.reply_text(f"🌐 Performing reverse lookup on `{escaped_ip}`...", parse_mode=ParseMode.MARKDOWN_V2)
    try:
        response = requests.get(REV_IP_API_URL, params={'ip': ip}, headers={'User-Agent': USER_AGENT}, timeout=45)
        response.raise_for_status()
        response_text = f"*Reverse IP Results for `{escaped_ip}`:*\n\n```\n{escape_markdown_v2(response.text)}\n```"
    except requests.RequestException as e:
        response_text = f"❌ API Error: {escape_markdown_v2(str(e))}"
    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)
