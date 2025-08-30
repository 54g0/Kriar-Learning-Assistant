# pip install yt-dlp
from yt_dlp import YoutubeDL

def ytdlp_metadata(url: str) -> dict:
    opts = {}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    # Select common fields; info contains many more keys
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "channel": info.get("channel"),
        "channel_id": info.get("channel_id"),
        "duration": info.get("duration"),
        "description": info.get("description"),
    }

print(ytdlp_metadata("https://www.youtube.com/watch?v=Gu1LpctEYZA&t=2477s"))
