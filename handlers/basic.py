from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from utils import get_bot_branding

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(rf"Hi {user.mention_html()}! 👋")
    await update.message.reply_text(get_bot_branding(), parse_mode=ParseMode.MARKDOWN_V2)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_bot_branding(), parse_mode=ParseMode.MARKDOWN_V2)
