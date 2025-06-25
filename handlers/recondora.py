# 666-main/handlers/recondora.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import aiohttp
import asyncio

# Import the shared logic from Web.py
from Web import ENDPOINTS, TOOL_GROUPS, parse_tool_input, fetch_tool
from utils import escape_markdown_v2, send_long_message

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
    # Use the centralized parser, defaulting to 'basic' if no tools are provided.
    tool_inputs = context.args[1:] if len(context.args) > 1 else ["basic"]
    tools_to_run = parse_tool_input(tool_inputs)

    if not tools_to_run:
        await update.message.reply_text(escape_markdown_v2("No valid tools or groups selected. Please check the command and try again."), parse_mode=ParseMode.MARKDOWN_V2)
        return

    escaped_domain = escape_markdown_v2(domain)
    escaped_tools = escape_markdown_v2(", ".join(tools_to_run))
    status_text = f"🔎 Running recon on `{escaped_domain}` with tools: `{escaped_tools}`{escape_markdown_v2('...')} this may take a moment\\."
    status_msg = await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN_V2)

    # Replaced the emoji here
    full_report = [f">_ *Recon Report for `{escaped_domain}`*"]
    
    async with aiohttp.ClientSession() as session:
        # Use the centralized fetch_tool function
        tasks = [fetch_tool(session, domain, tool) for tool in tools_to_run]
        results = await asyncio.gather(*tasks)

    for tool, result_text in results:
        # Format each section
        section = [
            f"\n\n*{escape_markdown_v2(f'[{tool.upper()}]')}*",
            f"```\n{result_text}\n```"
        ]
        full_report.extend(section)
    
    await status_msg.delete()
    await send_long_message(update, context, "\n".join(full_report), parse_mode=ParseMode.MARKDOWN_V2)
