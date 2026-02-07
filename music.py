import requests
import vlc
import time
import random

# Constants
LASTFM_API_KEY = '3852c780a1d584dd6528dbdaf6f74b57'

# Low Energy >> music to boost energy and motivation
# Deep Focus >> music to enhance concentration and block distractions
# High Stress >> music to lower heart rate and calm down

FocusTags = {
    "low_energy": ["upbeat", "electro", "motivation", "energetic", "dance"],
    "deep_focus": ["alphawaves", "instrumental", "focus"],
    "high_stress": ["chillout", "relax", "calm"],
}

def get_song_url(mood_tag):
# Fetch a song URL based on the mood tag

    lfm_url = f"https://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={mood_tag}&api_key={LASTFM_API_KEY}&format=json&limit=1"
    
    data = requests.get(lfm_url).json()
    track = data['tracks']['track'][0]
    query = f"{track['name']} {track['artist']['name']}"
    
    itunes_url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
    itunes_data = requests.get(itunes_url).json()
    return itunes_data['results'][0]['previewUrl']

def play_stream(url):
    # Create the player
    instance = vlc.Instance('--quiet', '--no-xlib')
    player = vlc.MediaPlayer(url)
    
    # Start playback
    
    player.play()
    
    print("Music is streaming... (VLC)")
    
    # Wait for the player to start and check if it's playing
    time.sleep(1) 
    while player.is_playing():
        time.sleep(1)
        

def main_loop():
    current_player = None
    last_mood = None

    while True:
        
        level = int(input("Enter Focus (1-10): ")) # This will be replaced by actual monitoring from Presage
        
        # Determine the mood based on the focus level
        if level < 3: 
            mood = random.choice(FocusTags["low_energy"])
        elif level < 7:
            mood = random.choice(FocusTags["deep_focus"])
        else:
            mood = random.choice(FocusTags["high_stress"])

        # Only change the song if the mood actually changed
        if mood != last_mood:
            if current_player:
                current_player.stop() # Stop the old song
            
            # Fetch and play the new song
            print(f"Switching to {mood} music...")
            url = get_song_url(level)
            current_player = vlc.MediaPlayer(url)
            current_player.play()
            last_mood = mood
        else:
            print("Mood same as before, keeping the vibe.")

if __name__ == "__main__":
    main_loop()
