import requests
import webbrowser

LASTFM_API_KEY = '3852c780a1d584dd6528dbdaf6f74b57'

def get_mood_music(focus_level):
    # Logic: Lower focus = more "ambient/calm". Higher focus = "lo-fi/upbeat"
    if focus_level < 4:
        tag = "ambient"
    elif focus_level < 8:
        tag = "lo-fi"
    else:
        tag = "focus"

    # 1. Get track from Last.fm
    lfm_url = f"https://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={tag}&api_key={LASTFM_API_KEY}&format=json&limit=5"
    
    try:
        data = requests.get(lfm_url).json()
        track = data['tracks']['track'][0]
        search_query = f"{track['name']} {track['artist']['name']}"
        
        # 2. Get playable link from iTunes
        itunes_url = f"https://itunes.apple.com/search?term={search_query}&entity=song&limit=1"
        itunes_data = requests.get(itunes_url).json()

        if itunes_data['results']:
            preview_url = itunes_data['results'][0]['previewUrl']
            print(f"Match found! Playing: {search_query}")
            
            # 3. Play the 30s preview in the browser
            webbrowser.open(preview_url)
        else:
            print("Could not find a playable preview.")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print(data)

# Example: Student is struggling to focus (Level 2)
get_mood_music(2)
