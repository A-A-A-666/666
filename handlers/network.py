# handlers/network.py

import whois
import dns.resolver
import subprocess
import re
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Optional, Tuple, Any, Dict, List
from utils import escape_markdown_v2, send_long_message, is_tool_installed

# --- Config ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REV_IP_API_URL = "https://api.hackertarget.com/reverseiplookup/"

# --- Internal Helper for /headers ---
def _get_header_data(domain: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        ipv4 = [ip.to_text() for ip in dns.resolver.resolve(domain, 'A')]
        ipv6: List[str] = []
        try:
            ipv6 = [ip.to_text() for ip in dns.resolver.resolve(domain, 'AAAA')]
        except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            pass

        headers: Dict[str, str] = {}
        final_url = f"https://{domain}"
        try:
            response = requests.get(final_url, timeout=10, headers={'User-Agent': USER_AGENT}, allow_redirects=True)
            headers = response.headers
            final_url = response.url
        except requests.RequestException:
            try:
                final_url = f"http://{domain}"
                response = requests.get(final_url, timeout=10, headers={'User-Agent': USER_AGENT}, allow_redirects=True)
                headers = response.headers
                final_url = response.url
            except requests.RequestException:
                pass

        return {"domain": domain, "final_url": final_url, "ipv4": ipv4, "ipv6": ipv6, "headers": dict(headers)}, None
    except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.resolver.Timeout) as e:
        return None, f"Could not resolve domain: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

# --- Command Handlers (Corrected) ---

async def nmap_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_tool_installed('nmap'):
        await update.message.reply_text(escape_markdown_v2("⚠️ Nmap is not installed on the server."), parse_mode=ParseMode.MARKDOWN_V2)
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
    
    # **FIX APPLIED HERE**: Escaped the "..."
    sent_message = await update.message.reply_text(f"Starting Nmap scan on `{escape_markdown_v2(target)}`{escape_markdown_v2('...')} This can take up to 5 minutes.", parse_mode=ParseMode.MARKDOWN_V2)
    
    command = ['nmap'] + user_flags + [target]
    response_text = ""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        output = result.stdout or result.stderr or "Scan completed with no output."
        response_text = f"*Nmap Scan Results for `{escape_markdown_v2(target)}`*\n\n```\n{escape_markdown_v2(output)}\n```"
        await sent_message.delete()
        await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2)
    except subprocess.TimeoutExpired:
        response_text = escape_markdown_v2(f"❌ Scan timed out after 5 minutes for target: {target}")
        await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        response_text = escape_markdown_v2(f"❌ Nmap scan error: {str(e)}")
        await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)

async def rustscan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_tool_installed('rustscan'):
        await update.message.reply_text(escape_markdown_v2("⚠️ RustScan is not installed on the server."), parse_mode=ParseMode.MARKDOWN_V2)
        return
    if not context.args:
        await update.message.reply_text(escape_markdown_v2("Usage: /rustscan <target>"), parse_mode=ParseMode.MARKDOWN_V2)
        return

    target = context.args[0]
    if not re.match(r"^[a-zA-Z0-9.-]+$", target):
        await update.message.reply_text(escape_markdown_v2("⚠️ Invalid target format."), parse_mode=ParseMode.MARKDOWN_V2)
        return
        
    # **FIX APPLIED HERE**: Escaped the "..."
    sent_message = await update.message.reply_text(f"Starting RustScan on `{escape_markdown_v2(target)}`{escape_markdown_v2('...')} This can take a moment.", parse_mode=ParseMode.MARKDOWN_V2)
    
    command = ['rustscan', '-a', target, '--ulimit', '5000', '--', '-sV']
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        output = result.stdout or result.stderr or "Scan completed with no output."
        cleaned_output = "\n".join([line for line in output.split('\n') if 'Starting Nmap' not in line and 'METADATA' not in line and 'ulimit' not in line])
        response_text = f"*RustScan Results for `{escape_markdown_v2(target)}`*\n\n```\n{escape_markdown_v2(cleaned_output)}\n```"
        await sent_message.delete()
        await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2)
    except subprocess.TimeoutExpired:
        response_text = escape_markdown_v2(f"❌ Scan timed out after 5 minutes for target: {target}")
        await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        response_text = escape_markdown_v2(f"❌ RustScan error: {str(e)}")
        await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)

async def lookup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text(escape_markdown_v2("Usage: /lookup <domain>"), parse_mode=ParseMode.MARKDOWN_V2); return
    
    domain = context.args[0].lower().strip().replace("http://", "").replace("https://", "")
    escaped_domain = escape_markdown_v2(domain)
    # **FIX APPLIED HERE**: Escaped the "..."
    sent_message = await update.message.reply_text(f"🕵️ Digging deep into `{escaped_domain}`{escape_markdown_v2('...')}", parse_mode=ParseMode.MARKDOWN_V2)
    
    response_text = f"🔎 *Lookup Report for `{escaped_domain}`*\n" + escape_markdown_v2("----------------------------------------\n\n")
    
    try:
        w = whois.whois(domain)
        response_text += "*WHOIS Information:*\n"
        if w.domain_name:
            whois_details = {
                'Domain': w.domain_name, 'Registrar': w.registrar,
                'Creation Date': w.creation_date, 'Expiration Date': w.expiration_date,
                'Last Updated': w.updated_date, 'Name Servers': w.name_servers, 'Status': w.status,
            }
            for key, value in whois_details.items():
                if not value: continue
                if isinstance(value, list):
                    value_str = ", ".join(sorted([str(v) for v in value]))
                elif isinstance(value, datetime):
                    value_str = value.strftime('%Y-%m-%d')
                else:
                    value_str = str(value)
                response_text += f"  *{escape_markdown_v2(key)}:* `{escape_markdown_v2(value_str)}`\n"
        else:
            response_text += "  `No public WHOIS data found.`\n"
    except Exception as e:
        response_text += f"*WHOIS Information:*\n  `Error: {escape_markdown_v2(str(e))}`\n"
    
    response_text += "\n*DNS Records:*\n"
    has_dns_records = False
    for r_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']:
        try:
            answers = dns.resolver.resolve(domain, r_type)
            records = sorted([str(r).strip() for r in answers])
            if records:
                has_dns_records = True
                response_text += f"  *{escape_markdown_v2(r_type)}:*\n"
                for record in records: response_text += f"    `{escape_markdown_v2(record)}`\n"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
            pass
    if not has_dns_records:
        response_text += "  `No common DNS records found.`\n"

    await sent_message.delete()
    await send_long_message(update, context, response_text, parse_mode=ParseMode.MARKDOWN_V2)

async def headers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text(escape_markdown_v2("Usage: /headers <domain>"), parse_mode=ParseMode.MARKDOWN_V2); return
    
    domain = context.args[0].replace("http://", "").replace("https://", "").split("/")[0]
    escaped_domain = escape_markdown_v2(domain)
    # **FIX APPLIED HERE**: Escaped the "..."
    sent_message = await update.message.reply_text(f"📡 Getting headers for `{escaped_domain}`{escape_markdown_v2('...')}", parse_mode=ParseMode.MARKDOWN_V2)
    
    data, error = _get_header_data(domain)
    if error: await sent_message.edit_text(f"❌ Error: {escape_markdown_v2(error)}", parse_mode=ParseMode.MARKDOWN_V2); return
    
    if data:
        response_text = f"🌐 *Info for `{escaped_domain}`*\n"
        if data.get('final_url') and data['final_url'] != f"https://{domain}" and data['final_url'] != f"http://{domain}":
             response_text += f"\n*Final URL:* `{escape_markdown_v2(data['final_url'])}`"
        if data.get('ipv4'): response_text += f"\n*IPv4:* `{', '.join(data['ipv4'])}`"
        if data.get('ipv6'): response_text += f"\n*IPv6:* `{', '.join(data['ipv6'])}`"
        
        if data.get('headers'):
            headers_lower = {k.lower(): v for k, v in data['headers'].items()}
            security_headers = {
                'Strict-Transport-Security': 'strict-transport-security', 'Content-Security-Policy': 'content-security-policy',
                'X-Frame-Options': 'x-frame-options', 'X-Content-Type-Options': 'x-content-type-options',
                'Referrer-Policy': 'referrer-policy', 'Permissions-Policy': 'permissions-policy'
            }
            security_analysis = "\n\n*Security Header Analysis:*\n"
            for key, val in security_headers.items():
                icon = "✅" if val in headers_lower else "❌"
                security_analysis += f"  `{icon}` {escape_markdown_v2(key)}\n"
            response_text += security_analysis

            headers_str = "\n*Full HTTP Headers:*\n"
            for key, val in data['headers'].items():
                headers_str += f"*{escape_markdown_v2(key)}:* `{escape_markdown_v2(val)}`\n"
            
            if len(response_text + headers_str) > 4000:
                response_text += "\n\n_Full headers list is too long to display\\._"
            else:
                response_text += headers_str
        else:
            response_text += "\n\n_Could not retrieve HTTP headers\\._"

        await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)

async def methods_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text(escape_markdown_v2("Usage: /methods <url>"), parse_mode=ParseMode.MARKDOWN_V2); return
    url = context.args[0]
    if not re.match(r"^https?://", url): url = 'https://' + url
    
    escaped_url = escape_markdown_v2(url)
    # **FIX APPLIED HERE**: Escaped the "..."
    sent_message = await update.message.reply_text(f"🔎 Checking methods for `{escaped_url}`{escape_markdown_v2('...')}", parse_mode=ParseMode.MARKDOWN_V2)
    
    try:
        response = requests.options(url, timeout=10, headers={'User-Agent': USER_AGENT}, allow_redirects=True)
        allowed_methods = response.headers.get('Allow', 'Not Specified (OPTIONS may not be enabled)')
        response_text = f"📋 *Allowed Methods for `{escaped_url}`*\n`{escape_markdown_v2(allowed_methods)}`\n_(Status: {response.status_code})_"
    except requests.RequestException as e:
        response_text = f"❌ Could not connect to `{escaped_url}`.\n*Error:* `{escape_markdown_v2(str(e))}`"
    
    await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)

async def revip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text(escape_markdown_v2("Usage: /revip <ip_or_domain>"), parse_mode=ParseMode.MARKDOWN_V2); return
    
    query, escaped_query = context.args[0], escape_markdown_v2(context.args[0])
    # **FIX APPLIED HERE**: Escaped the "..."
    sent_message = await update.message.reply_text(f"🌐 Performing reverse lookup on `{escaped_query}`{escape_markdown_v2('...')}", parse_mode=ParseMode.MARKDOWN_V2)
    
    try:
        response = requests.get(REV_IP_API_URL, params={'q': query}, headers={'User-Agent': USER_AGENT}, timeout=45)
        response.raise_for_status()
        
        if "error check your search query" in response.text:
             response_text = f"❌ API Error: Invalid IP or domain provided: `{escaped_query}`"
        else:
             response_text = f"*Reverse IP Results for `{escaped_query}`:*\n\n```\n{escape_markdown_v2(response.text.strip())}\n```"
    except requests.RequestException as e:
        response_text = f"❌ API Error: {escape_markdown_v2(str(e))}"
    
    await sent_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)
