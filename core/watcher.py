import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.logger_config import logger

import time

import psutil

class RestartHandler(FileSystemEventHandler):
    _restarting = False

    def on_modified(self, event):
        if event.src_path.endswith((".py", ".env")):
            if RestartHandler._restarting:
                return
            
            RestartHandler._restarting = True
            logger.warning(f"RESTARTING: {event.src_path} modified.")
            
            # Beri jeda kecil agar file selesai ditulis
            time.sleep(1.0)
            
            # Cari dan bunuh proses bot lain yang mungkin masih hidup
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] != current_pid and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any('main.py' in arg for arg in cmdline):
                            logger.info(f"Terminating zombie bot process (PID: {proc.info['pid']})")
                            proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Jalankan proses baru dan matikan proses ini
            import subprocess
            subprocess.Popen([sys.executable] + sys.argv)
            os._exit(0)

def start_watcher():
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.daemon = True
    observer.start()
    logger.info("Hot Reload Watcher started.")
