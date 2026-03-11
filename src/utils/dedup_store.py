import json
import os

class DedupStore:
    def __init__(self, filename: str):
        self.filename = filename
        self.posted_urls = set()
        self._load()

    def _load(self):
        if not os.path.exists(self.filename):
            # Buat file dan foldernya jika belum ada
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            self._save()
            return
            
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.posted_urls = set(data.get('posted_urls', []))
        except (json.JSONDecodeError, FileNotFoundError):
            self.posted_urls = set()

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump({'posted_urls': list(self.posted_urls)}, f, indent=4)

    def is_posted(self, url: str) -> bool:
        return url in self.posted_urls

    def mark_posted(self, url: str):
        self.posted_urls.add(url)
        self._save()
