import requests
import vlc
import time
import random
import os
from dotenv import load_dotenv
from biometrics import BiometricsMonitor
import tkinter as tk
from tkinter import ttk
import threading

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

class MusicMonitorUI:
    """UI window to display current song, mood, and biometrics."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Focus Music Monitor")
        self.root.geometry("500x400")
        self.root.configure(bg='#1e1e1e')
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#1e1e1e', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="🎵 Focus Music System", 
                               font=('Arial', 20, 'bold'), 
                               bg='#1e1e1e', fg='#00d4ff')
        title_label.pack(pady=(0, 20))
        
        # Mood section
        mood_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15)
        mood_frame.pack(fill=tk.X, pady=10)
        
        mood_title = tk.Label(mood_frame, text="Current Mood", 
                             font=('Arial', 12, 'bold'), 
                             bg='#2d2d2d', fg='#888888')
        mood_title.pack()
        
        self.mood_label = tk.Label(mood_frame, text="--", 
                                   font=('Arial', 24, 'bold'), 
                                   bg='#2d2d2d', fg='#ffffff')
        self.mood_label.pack()
        
        # Song section
        song_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15)
        song_frame.pack(fill=tk.X, pady=10)
        
        song_title = tk.Label(song_frame, text="Now Playing", 
                             font=('Arial', 12, 'bold'), 
                             bg='#2d2d2d', fg='#888888')
        song_title.pack()
        
        self.song_label = tk.Label(song_frame, text="No song playing", 
                                   font=('Arial', 14), 
                                   bg='#2d2d2d', fg='#ffffff',
                                   wraplength=400)
        self.song_label.pack()
        
        self.artist_label = tk.Label(song_frame, text="", 
                                     font=('Arial', 11, 'italic'), 
                                     bg='#2d2d2d', fg='#aaaaaa')
        self.artist_label.pack()
        
        # Biometrics section
        bio_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15)
        bio_frame.pack(fill=tk.X, pady=10)
        
        bio_title = tk.Label(bio_frame, text="Biometric Data", 
                            font=('Arial', 12, 'bold'), 
                            bg='#2d2d2d', fg='#888888')
        bio_title.pack()
        
        # HR and Blinks in a grid
        metrics_frame = tk.Frame(bio_frame, bg='#2d2d2d')
        metrics_frame.pack(pady=5)
        
        # Heart Rate
        hr_container = tk.Frame(metrics_frame, bg='#2d2d2d')
        hr_container.grid(row=0, column=0, padx=20)
        
        tk.Label(hr_container, text="❤️ Heart Rate", 
                font=('Arial', 10), bg='#2d2d2d', fg='#888888').pack()
        self.hr_label = tk.Label(hr_container, text="-- BPM", 
                                font=('Arial', 18, 'bold'), 
                                bg='#2d2d2d', fg='#ff6b6b')
        self.hr_label.pack()
        
        # Blinks per minute
        blink_container = tk.Frame(metrics_frame, bg='#2d2d2d')
        blink_container.grid(row=0, column=1, padx=20)
        
        tk.Label(blink_container, text="👁️ Blink Rate", 
                font=('Arial', 10), bg='#2d2d2d', fg='#888888').pack()
        self.blink_label = tk.Label(blink_container, text="-- /min", 
                                   font=('Arial', 18, 'bold'), 
                                   bg='#2d2d2d', fg='#4ecdc4')
        self.blink_label.pack()
        
        # Status bar
        self.status_label = tk.Label(main_frame, text="Initializing...", 
                                     font=('Arial', 9), 
                                     bg='#1e1e1e', fg='#666666')
        self.status_label.pack(side=tk.BOTTOM, pady=(10, 0))
        
    def update_mood(self, mood):
        """Update the mood display."""
        mood_colors = {
            "low_energy": "#ffd93d",
            "deep_focus": "#6bcf7f",
            "high_stress": "#ff6b9d"
        }
        
        mood_names = {
            "low_energy": "🔋 Low Energy",
            "deep_focus": "🎯 Deep Focus",
            "high_stress": "😰 High Stress"
        }
        
        # Determine category
        category = None
        for cat, tags in FocusTags.items():
            if mood in tags:
                category = cat
                break
        
        if category:
            self.mood_label.config(text=mood_names.get(category, mood.upper()), 
                                  fg=mood_colors.get(category, "#ffffff"))
        else:
            self.mood_label.config(text=mood.upper(), fg="#ffffff")
    
    def update_song(self, track_name, artist_name):
        """Update the currently playing song."""
        self.song_label.config(text=track_name)
        self.artist_label.config(text=f"by {artist_name}")
    
    def update_biometrics(self, hr, blinks_per_min):
        """Update biometric data."""
        # Update heart rate with color coding
        if hr > 0:
            if hr > 100:
                hr_color = "#ff4757"  # Red for high
            elif hr < 60:
                hr_color = "#ffa502"  # Orange for low
            else:
                hr_color = "#2ed573"  # Green for normal
            self.hr_label.config(text=f"{hr:.0f} BPM", fg=hr_color)
        else:
            self.hr_label.config(text="-- BPM", fg="#666666")
        
        # Update blink rate with color coding
        if blinks_per_min > 0:
            if blinks_per_min > 20:
                blink_color = "#ff4757"  # Red for high
            elif blinks_per_min < 10:
                blink_color = "#ffa502"  # Orange for low
            else:
                blink_color = "#2ed573"  # Green for normal
            self.blink_label.config(text=f"{blinks_per_min:.1f} /min", fg=blink_color)
        else:
            self.blink_label.config(text="-- /min", fg="#666666")
    
    def update_status(self, status):
        """Update status bar text."""
        self.status_label.config(text=status)
    
    def run(self):
        """Start the UI main loop."""
        self.root.mainloop()
    
    def destroy(self):
        """Close the window."""
        self.root.quit()


def get_song_url(mood_tag):
    # Fetch a song URL based on the mood tag
    
    lfm_url = f"https://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={mood_tag}&api_key={LASTFM_API_KEY}&format=json&limit=1"
    
    data = requests.get(lfm_url).json()
    track = data['tracks']['track'][0]
    query = f"{track['name']} {track['artist']['name']}"
    
    itunes_url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
    itunes_data = requests.get(itunes_url).json()
    
    return itunes_data['results'][0]['previewUrl'], track['name'], track['artist']['name']


def music_loop(ui, bio_monitor):
    """Music control loop that runs in a separate thread."""
    current_player = None
    last_mood = None
    current_track_name = ""
    current_artist_name = ""
    
    # Give the monitor a moment to initialize
    time.sleep(2)
    ui.update_status("Monitoring biometrics...")
    
    try:
        while True:
            # Get real biometric data from the monitor
            hr, blinks_per_min = bio_monitor.get_metrics()
            
            # Update UI with current biometrics
            ui.update_biometrics(hr, blinks_per_min)
            
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
                ui.update_status(f"Loading {mood} music...")
                
                try:
                    url, track_name, artist_name = get_song_url(mood)
                    current_player = vlc.MediaPlayer(url)
                    current_player.play()
                    
                    current_track_name = track_name
                    current_artist_name = artist_name
                    
                    # Update UI
                    ui.update_mood(mood)
                    ui.update_song(track_name, artist_name)
                    ui.update_status(f"Playing {mood} music")
                    
                    last_mood = mood
                except Exception as e:
                    print(f"Error loading song: {e}")
                    ui.update_status(f"Error loading song")
            else:
                print(f"Mood same ({mood}). HR={hr:.1f}, blinks/min={blinks_per_min:.1f}")
            
            # Check metrics every 5 seconds
            time.sleep(5)
            
    except Exception as e:
        print(f"Music loop error: {e}")
    finally:
        # Clean shutdown
        if current_player:
            current_player.stop()


def main():
    # Create UI
    ui = MusicMonitorUI()
    
    # Initialize the biometrics monitor
    bio_monitor = BiometricsMonitor()
    bio_monitor.start()
    
    print("Starting biometrics monitoring...")
    ui.update_status("Starting biometrics monitoring...")
    
    # Start music loop in separate thread
    music_thread = threading.Thread(target=music_loop, args=(ui, bio_monitor), daemon=True)
    music_thread.start()
    
    try:
        # Run UI (blocks until window closed)
        ui.run()
    except KeyboardInterrupt:
        print("\nStopping music and biometrics monitoring...")
    finally:
        # Clean shutdown
        bio_monitor.stop()
        print("Shutdown complete")


if __name__ == "__main__":
    main()