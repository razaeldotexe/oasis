import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.logger_config import logger

class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith((".py", ".env")):
            logger.warning(f"RESTARTING: {event.src_path} modified.")
            os.execv(sys.executable, ['python'] + sys.argv)

def start_watcher():
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.daemon = True
    observer.start()
    logger.info("Hot Reload Watcher started.")
