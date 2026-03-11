import aiohttp
from core.logger_config import logger

TRIBUN_API = "https://api.siputzx.my.id/api/berita/tribunnews"

async def fetch_latest_news() -> list[dict]:
    """Mengambil berita terbaru dari Tribun News API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(TRIBUN_API, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # API siputzx mengembalikan { "status": true, "data": [...] }
                    return data.get("data", [])
                else:
                    logger.error(f"Failed to fetch news. Status code: {resp.status}")
    except Exception as e:
        logger.error(f"Error fetching news from API: {e}")
        
    return []
