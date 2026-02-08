import requests
import vlc
import time
import random
import os
from dotenv import load_dotenv
from biometrics import BiometricsMonitor

# Load the variables from the .env file into the system environment
load_dotenv()

# Use os.getenv to grab the specific variable
api_key = os.getenv("LASTFM_API_KEY")

# Constants
LASTFM_API_KEY = api_key

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
    # Initialize the biometrics monitor
    bio_monitor = BiometricsMonitor()
    bio_monitor.start()
    
    # Give the monitor a moment to initialize and start collecting data
    print("Starting biometrics monitoring...")
    time.sleep(2)
    
    current_player = None
    last_mood = None

    try:
        while True:
            # Get real biometric data from the monitor
            hr, blinks_per_min = bio_monitor.get_metrics()
            
            print(f"Current metrics - HR: {hr:.1f} BPM, Blinks/min: {blinks_per_min:.1f}")
            
            # Heuristic mapping from metrics to mood tag
            if hr > 95 or blinks_per_min > 20:
                mood = random.choice(FocusTags["high_stress"])
            elif 12 <= blinks_per_min <= 20 and 50 <= hr <= 95:
                mood = random.choice(FocusTags["deep_focus"])
            elif hr < 50 and blinks_per_min < 12:
                mood = random.choice(FocusTags["low_energy"])
            else:
                mood = random.choice(FocusTags["deep_focus"])

            # Only change the song if the mood actually changed
            if mood != last_mood:
                if current_player:
                    current_player.stop()  # Stop the old song
                
                # Fetch and play the new song
                print(f"Switching to {mood} music... (HR={hr:.1f}, blinks/min={blinks_per_min:.1f})")
                url = get_song_url(mood)
                current_player = vlc.MediaPlayer(url)
                current_player.play()
                last_mood = mood
            else:
                print(f"Mood same ({mood}). HR={hr:.1f}, blinks/min={blinks_per_min:.1f}")
            
            # Check metrics every 5 seconds
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nStopping music and biometrics monitoring...")
    finally:
        # Clean shutdown
        if current_player:
            current_player.stop()
        bio_monitor.stop()


if __name__ == "__main__":
    main_loop()