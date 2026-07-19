"""
YouTube tool — read-only search.

Setup:
1. Go to https://console.cloud.google.com/ -> create a project (free)
2. Enable "YouTube Data API v3"
3. Create an API key (APIs & Services -> Credentials)
4. Put it in core/.env as YOUTUBE_API_KEY=...

Free tier: 10,000 units/day. Each search costs ~100 units, so ~100 searches/day free.
"""

import requests
from config import YOUTUBE_API_KEY

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search_youtube(query: str, max_results: int = 5) -> list[dict]:
    """Returns a list of {title, channel, video_id, url, description} for a search query."""
    if not YOUTUBE_API_KEY:
        return [{"error": "YOUTUBE_API_KEY not set in core/.env"}]

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }

    try:
        res = requests.get(SEARCH_URL, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.RequestException as e:
        return [{"error": f"YouTube request failed: {e}"}]

    results = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        results.append({
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "description": snippet["description"],
        })
    return results


# Quick manual test: `python core/tools/youtube.py`
if __name__ == "__main__":
    for r in search_youtube("lo-fi study beats"):
        print(r)