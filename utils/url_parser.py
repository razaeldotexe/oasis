import re

def extract_video_id(url: str) -> str | None:
    """
    Ekstrak YouTube Video ID dari berbagai format URL.
    
    Mendukung:
    - Standard: https://www.youtube.com/watch?v=VIDEO_ID
    - Short: https://youtu.be/VIDEO_ID
    - Shorts: https://www.youtube.com/shorts/VIDEO_ID
    - Music: https://music.youtube.com/watch?v=VIDEO_ID
    - Mobile: https://m.youtube.com/watch?v=VIDEO_ID
    """
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/embed\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
    return None
