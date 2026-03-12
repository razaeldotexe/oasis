import os
import asyncio
import signal
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

        async def shutdown(sig, loop):
            logger.info(f"Menerima sinyal {sig.name}, menghentikan bot...")
            await bot.close()
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            [task.cancel() for task in tasks]
            logger.info("Membatalkan task yang tersisa...")
            await asyncio.gather(*tasks, return_exceptions=True)
            loop.stop()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))

        try:
            logger.info("Starting Oasis Bot...")
            bot.run(TOKEN, log_handler=None)
        except Exception as e:
            logger.error(f"Terjadi kesalahan saat menjalankan bot: {e}")
        finally:
            logger.info("Bot dimatikan.")
