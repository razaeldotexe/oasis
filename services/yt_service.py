import yt_dlp
import asyncio
from typing import Dict, Any, List

async def get_thumbnail_info(video_id: str, cookiefile: str | None = None) -> Dict[str, Any]:
    """
    Ambil metadata dan info thumbnail video YouTube menggunakan yt-dlp.
    Fungsi ini dijalankan di thread terpisah agar tidak memblokir event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_info, video_id, cookiefile)

def _extract_info(video_id: str, cookiefile: str | None = None) -> Dict[str, Any]:
    """Sinkronus wrapper untuk yt-dlp extract_info."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
        'ignoreerrors': True, 
        'noplaylist': True,
        'check_formats': False, # PENTING: Jangan cek format video
        'ignore_no_formats_error': True, # PENTING: Abaikan jika format video tidak ada
    }

    if cookiefile:
        if cookiefile.startswith("browser:"):
            ydl_opts['cookiesfrombrowser'] = (cookiefile.split(":")[1],)
        else:
            ydl_opts['cookiefile'] = cookiefile

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                raise Exception("Gagal mengambil informasi video. Pastikan cookies valid dan video tersedia.")

            # Petakan thumbnail
            thumbnails = info.get('thumbnails', [])
            mapped_thumbnails = _map_thumbnails(thumbnails, video_id)
            
            return {
                "metadata": {
                    "video_id": video_id,
                    "title": info.get('title', 'Unknown Title'),
                    "author": info.get('uploader') or info.get('channel') or 'Unknown Author',
                    "description": info.get('description', ''),
                    "duration": info.get('duration', 0),
                    "view_count": info.get('view_count', 0)
                },
                "thumbnails": mapped_thumbnails
            }
        except Exception as e:
            raise e

def _map_thumbnails(thumbnails: List[Dict[str, Any]], video_id: str) -> Dict[str, str]:
    """
    Memetakan list thumbnails dari yt-dlp ke resolusi yang diinginkan.
    Jika tidak ditemukan, gunakan URL format standar YouTube.
    """
    # Resolusi target
    resolutions = {
        'default': 'default',
        'medium': 'mqdefault',
        'high': 'hqdefault',
        'max_res': 'maxresdefault'
    }
    
    result = {}
    for key, suffix in resolutions.items():
        # Coba cari di data yt-dlp terlebih dahulu (opsional, tapi lebih akurat)
        # Sebagai fallback yang reliable untuk API thumbnail YouTube:
        result[key] = f"https://img.youtube.com/vi/{video_id}/{suffix}.jpg"
        
    return result
