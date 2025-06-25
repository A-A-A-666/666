# 666-main/handlers/recondora.py

import asyncio
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils import escape_markdown_v2, send_long_message

# === API TARGETS (from original script) ===
ENDPOINTS = {
    "hostsearch": "https://api.hackertarget.com/hostsearch/?q=",
    "dnslookup": "https://api.hackertarget.com/dnslookup/?q=",
    "findshareddns": "https://api.hackertarget.com/findshareddns/?q=",
    "reverseiplookup": "https://api.hackertarget.com/reverseiplookup/?q=",
    "zonetransfer": "https://api.hackertarget.com/zonetransfer/?q=",
    "httpheaders": "https://api.hackertarget.com/httpheaders/?q=",
    "nmap": "https://api.hackertarget.com/nmap/?q=",
    "pagelinks": "https://api.hackertarget.com/pagelinks/?q=",
    "whois": "https://api.hackertarget.com/whois/?q=",
    "mtr": "https://api.hackertarget.com/mtr/?q=",
    "geoip": "https://api.hackertarget.com/geoip/?q=",
    "aslookup": "https://api.hackertarget.com/aslookup/?q="
}

TOOL_GROUPS = {
    "basic": ["hostsearch", "dnslookup", "whois"],
    "network": ["nmap", "mtr", "geoip", "aslookup"],
    "web": ["httpheaders", "pagelinks"],
    "dns": ["hostsearch", "dnslookup", "findshareddns", "zonetransfer", "reverseiplookup"],
    "all": list(ENDPOINTS.keys()) # Adding an 'all' group for convenience
}

# === Helper Functions (from original script, adapted) ===
def _parse_tool_input(tool_inputs: list[str]) -> list[str]:
    """Parses user input into a final list of tools to run."""
    final_tools = set()
    for item in tool_inputs:
        item = item.lower()
        if item in ENDPOINTS:
            final_tools.add(item)
        elif item in TOOL_GROUPS:
            final_tools.update(TOOL_GROUPS[item])
    # Return a sorted list for consistent execution order
    return sorted(list(final_tools))

async def _fetch_tool(session: aiohttp.ClientSession, domain: str, tool: str) -> tuple[str, str]:
    """Fetches data from a single HackerTarget API endpoint."""
    try:
        url = ENDPOINTS[tool] + domain
        # Setting a reasonable user-agent
        headers = {'User-Agent': 'Doraemon-Telegram-Bot/1.0'}
        async with session.get(url, timeout=45, headers=headers) as resp:
            resp.raise_for_status() # Raise an exception for bad status codes
            text_content = await resp.text()
            if "error check your search query" in text_content:
                return tool, "API Error: Invalid domain or query."
            return tool, text_content
    except aiohttp.ClientError as e:
        return tool, f"[API Request Error] {e}"
    except asyncio.TimeoutError:
        return tool, "[API Request Error] Request timed out after 45 seconds."
    except Exception as e:
        return tool, f"[Unexpected Error] {e}"

# === Command Handler ===
async def recon_doraemon_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Performs reconnaissance on a domain using multiple HackerTarget API endpoints.
    """
    if not context.args:
        # Provide detailed usage info
        tool_list_str = escape_markdown_v2(", ".join(ENDPOINTS.keys()))
        group_list_str = escape_markdown_v2(", ".join(TOOL_GROUPS.keys()))
        
        usage_text = (
            "Perform multi\\-tool reconnaissance on a domain\\.\n\n"
            "*Usage:* `/recondora <domain> [tool/group1] [tool/group2] ...`\n\n"
            "*Example:* `/recondora example.com basic web`\n\n"
            "If no tools or groups are specified, the `basic` group is used by default\\.\n\n"
            f"*Available Tools:*\n`{tool_list_str}`\n\n"
            f"*Available Groups:*\n`{group_list_str}`"
        )
        await update.message.reply_text(usage_text, parse_mode=ParseMode.MARKDOWN_V2)
        return

    domain = context.args[0]
    tool_inputs = context.args[1:] if len(context.args) > 1 else ["basic"]

    tools_to_run = _parse_tool_input(tool_inputs)

    if not tools_to_run:
        await update.message.reply_text("No valid tools or groups selected. Please check the command and try again.")
        return

    escaped_domain = escape_markdown_v2(domain)
    escaped_tools = escape_markdown_v2(", ".join(tools_to_run))
    status_msg = await update.message.reply_text(
        f"🔎 Running recon on `{escaped_domain}` with tools: `{escaped_tools}`\\.\\.\\. this may take a moment\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    full_report = [f"🐱‍💻 *Recon Report for `{escaped_domain}`*"]
    
    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_tool(session, domain, tool) for tool in tools_to_run]
        results = await asyncio.gather(*tasks)

    for tool, result_text in results:
        # Format each section
        section = [
            f"\n\n*{escape_markdown_v2(f'[{tool.upper()}]')}*",
            f"```\n{result_text.strip()}\n```"
        ]
        full_report.extend(section)
    
    # Delete the "loading" message and send the final report
    await status_msg.delete()
    await send_long_message(update, context, "\n".join(full_report), parse_mode=ParseMode.MARKDOWN_V2)
