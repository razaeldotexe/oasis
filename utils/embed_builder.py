import discord
from datetime import datetime

def build_news_embed(article: dict) -> discord.Embed:
    """Membentuk object discord.Embed berdasarkan data berita."""
    # Menghindari KeyError dengan penggunaan dict.get
    title = article.get("title", "Berita Terbaru")
    link = article.get("link", "")
    desc = article.get("description", "")
    
    # Batasi panjang description maksimal 300 karakter untuk mencegah spam yang berlebihan
    if len(desc) > 300:
        desc = desc[:297] + "..."

    embed = discord.Embed(
        title=title,
        url=link,
        description=desc,
        color=0xE63946,  # Warna Merah yang identik dengan merek Tribun News
        timestamp=datetime.utcnow()
    )

    thumbnail = article.get("thumbnail")
    if thumbnail:
        embed.set_image(url=thumbnail)

    embed.set_footer(text="📰 Tribun News", icon_url="https://tribunnews.com/favicon.ico")
    return embed
