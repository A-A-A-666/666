# 666-main/handlers/recondora.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import aiohttp
import asyncio

# Import the core execution logic from Web.py
from Web import ENDPOINTS, LOCAL_TOOLS, fetch_tool, run_local_tool
# Import the new helper functions and templates
from .bot_helpers import resolve_tools_from_args, format_telegram_report
from .bot_templates import get_recondora_help_text, get_status_message
from utils import send_long_message

async def recon_doraemon_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /recondora command by orchestrating helpers and core logic.
    """
    # 1. Handle arguments and help text
    if not context.args:
        await update.message.reply_text(get_recondora_help_text(), parse_mode=ParseMode.MARKDOWN_V2)
        return

    domain = context.args[0]
    tools_to_run = resolve_tools_from_args(context.args[1:])
    
    if not tools_to_run:
        await update.message.reply_text("No valid tools found for your selection. Please check the command and try again.")
        return

    # 2. Send status message
    status_msg = await update.message.reply_text(
        get_status_message(domain, sorted(list(tools_to_run))),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    # 3. Execute tasks
    api_coroutines = []
    local_coroutines = []
    async with aiohttp.ClientSession() as session:
        for tool_key in tools_to_run:
            if tool_key in ENDPOINTS:
                api_coroutines.append(fetch_tool(session, domain, tool_key))
            elif tool_key in LOCAL_TOOLS:
                local_coroutines.append(run_local_tool(domain, tool_key))
        
        results = await asyncio.gather(*api_coroutines, *local_coroutines)

    # 4. Format and send the final report
    final_report = format_telegram_report(domain, results)
    
    await status_msg.delete()
    await send_long_message(update, context, final_report, parse_mode=ParseMode.MARKDOWN_V2)
