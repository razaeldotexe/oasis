import asyncio
import click
import httpx
import os
from pathlib import Path
from utils.url_parser import extract_video_id
from services.yt_service import get_thumbnail_info

# Warna untuk output terminal
def success_msg(text): return click.style(text, fg="green", bold=True)
def error_msg(text): return click.style(text, fg="red", bold=True)
def info_msg(text): return click.style(text, fg="cyan")

async def download_image(url: str, path: Path) -> tuple[bool, int]:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                path.parent.mkdir(parents=True, exist_ok=True) # Ensure parent directory exists
                with open(path, "wb") as f:
                    f.write(resp.content)
                return True, 200
            return False, resp.status_code
    except Exception:
        return False, 0

@click.command()
@click.argument("url")
@click.option("--quality", "-q", default="max", type=click.Choice(["low", "medium", "high", "max"]), help="Kualitas thumbnail (default: max)")
@click.option("--output", "-o", default="downloads", help="Folder tujuan penyimpanan (default: downloads)")
@click.option("--cookies", "-c", default=None, help="Path ke file cookies YouTube (.txt format Netscape)")
@click.option("--browser", "-b", default=None, help="Ambil cookies langsung dari browser (contoh: chrome, edge, firefox)")
def main(url, quality, output, cookies, browser):
    """
    YT Thumbnail Downloader CLI 🚀
    
    Unduh thumbnail YouTube langsung dari terminal.
    Mendukung Windows, macOS, Linux, dan Android (Termux).
    """
    asyncio.run(run_cli(url, quality, output, cookies, browser))

async def run_cli(url, quality, output, cookies, browser):
    click.echo(info_msg(f"🔍 Memproses URL: {url}..."))
    
    video_id = extract_video_id(url)
    if not video_id:
        click.echo(error_msg("❌ URL tidak valid atau Video ID tidak ditemukan."))
        return

    try:
        # Tentukan sumber cookies
        cookie_src = cookies
        if browser:
            # Note: get_thumbnail_info perlu update parameter jika ingin support ini secara elegan, 
            # tapi untuk sekarang kita bisa bypass via ydl_opts di service.
            cookie_src = f"browser:{browser}"

        # Ambil info metadata dan thumbnail
        info = await get_thumbnail_info(video_id, cookiefile=cookie_src)
        metadata = info["metadata"]
        thumbnails = info["thumbnails"]

        click.echo(success_msg(f"✅ Video ditemukan: {metadata['title']}"))
        click.echo(info_msg(f"👤 Author: {metadata['author']}"))

        # Pilih URL berdasarkan kualitas
        quality_map = {
            "low": "default",
            "medium": "medium",
            "high": "high",
            "max": "max_res"
        }
        
        img_url = thumbnails[quality_map[quality]]
        
        # Nama file aman
        clean_title = "".join([c if c.isalnum() else "_" for c in metadata['title']])[:50]
        filename = f"{clean_title}_{quality}.jpg"
        save_path = Path(output) / filename

        click.echo(info_msg(f"📥 Mengunduh thumbnail ({quality})..."))
        
        success = await download_image(img_url, save_path)
        success, status_code = await download_image(img_url, save_path)
        
        if success:
            click.echo(success_msg(f"⭐ Selesai! Disimpan di: {save_path.absolute()}"))
        else:
            # Fallback jika max_res tidak tersedia
            if quality == "max":
                click.echo(info_msg("⚠️  Kualitas 'max' tidak tersedia, mencoba kualitas 'high'..."))
                img_url = thumbnails["high"]
                success, status_code = await download_image(img_url, save_path)
                if success:
                    click.echo(success_msg(f"⭐ Selesai! Disimpan di: {save_path.absolute()}"))
                    return

            if status_code:
                click.echo(error_msg(f"❌ Gagal mengunduh gambar (Status: {status_code})."))
            else:
                click.echo(error_msg("❌ Gagal mengunduh gambar."))

    except Exception as e:
        click.echo(error_msg(f"❌ Terjadi kesalahan: {str(e)}"))

if __name__ == "__main__":
    main()
