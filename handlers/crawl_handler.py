import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.crawler import AdvancedCrawler
from services.injection_scanner import scan_for_injections
from services.report_generator import generate_vulnerability_report

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def crawl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"User {user_id} initiated crawl command")
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /crawl <url> [--depth=2] [--max-pages=10]")
        return
        
    target_url = context.args[0].strip()
    depth = 2
    max_pages = 10
    
    # Parse optional arguments
    for arg in context.args[1:]:
        if arg.startswith("--depth="):
            depth = int(arg.split("=")[1])
        elif arg.startswith("--max-pages="):
            max_pages = int(arg.split("=")[1])
    
    try:
        # Initialize crawler
        crawler = AdvancedCrawler(
            base_url=target_url,
            max_depth=depth,
            max_pages=max_pages
        )
        
        # Start crawling
        msg = await update.message.reply_text(f"🕷️ Crawling {target_url} (depth: {depth}, max pages: {max_pages})...")
        
        await crawler.crawl()
        crawled_urls = crawler.get_discovered_urls()
        
        # Scan for vulnerabilities
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=f"🔍 Scanning {len(crawled_urls)} URLs for injection points..."
        )
        
        vulnerabilities = await scan_for_injections(crawled_urls)
        
        # Generate report
        report = generate_vulnerability_report(vulnerabilities)
        
        # Send results
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=report[:4000]  # Telegram message limit
        )
        
        if len(report) > 4000:
            await update.effective_chat.send_message(report[4000:8000])
            
    except Exception as e:
        logger.error(f"Crawl error: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")