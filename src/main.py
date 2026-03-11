import os
from dotenv import load_dotenv
from core.bot import OasisBot
from core.watcher import start_watcher
from core.logger_config import logger

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if __name__ == "__main__":
    if not TOKEN:
        logger.critical("No token found in .env!")
    else:
        start_watcher()
        bot = OasisBot()
        logger.info("Starting Oasis Bot...")
        bot.run(TOKEN, log_handler=None)
