
import requests
import webbrowser

LASTFM_API_KEY = "3852c780a1d584dd6528dbdaf6f74b57"

FOCUS_TAGS = {
    "low": ["ambient", "calm", "chillout", "relax", "meditation"],
    "medium": ["lofi", "lo-fi", "chillhop", "instrumental", "study"],
    "high": ["focus", "deep focus", "classical", "piano", "soundtrack"]
}

def get_mood_music(focus_level):
    # Choose tag group based on focus
    if focus_level < 4:
        tags = FOCUS_TAGS["low"]
    elif focus_level < 8:
        tags = FOCUS_TAGS["medium"]
    else:
        tags = FOCUS_TAGS["high"]

    try:
        for tag in tags:
            print(f"Trying tag: {tag}")

            # 1. Get tracks from Last.fm
            lfm_url = (
                "https://ws.audioscrobbler.com/2.0/"
                f"?method=tag.gettoptracks&tag={tag}"
                f"&api_key={LASTFM_API_KEY}&format=json&limit=5"
            )

            data = requests.get(lfm_url, timeout=10).json()

            tracks = data.get("tracks", {}).get("track", [])
            if not tracks:
                continue

            for track in tracks:
                name = track.get("name")
                artist = track.get("artist", {}).get("name")

                if not name or not artist:
                    continue

                search_query = f"{name} {artist}"

                # 2. Search iTunes for preview
                itunes_url = (
                    "https://itunes.apple.com/search"
                    f"?term={search_query}&entity=song&limit=1"
                )

                itunes_data = requests.get(itunes_url, timeout=10).json()
                results = itunes_data.get("results", [])

                if results and "previewUrl" in results[0]:
                    preview_url = results[0]["previewUrl"]
                    print(f"Match found! Playing: {search_query} (tag: {tag})")
                    webbrowser.open(preview_url)
                    return

        print("No playable preview found for any tag.")

    except Exception as e:
        print(f"Error: {e}")

# Example: Student is struggling to focus
get_mood_music(2)


