from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import time
import random
import os
from dotenv import load_dotenv
from biometrics import BiometricsMonitor
import threading
from collections import deque
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("LASTFM_API_KEY")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Constants
LASTFM_API_KEY = api_key
SONG_DURATION = 30  # iTunes preview duration in seconds

FocusTags = {
    "low_energy": ["upbeat", "electro", "motivation", "energetic", "dance"],
    "deep_focus": ["alphawaves", "instrumental", "focus"],
    "high_stress": ["chillout", "relax", "calm"],
}

# Global state
bio_monitor = None
monitoring_active = False
current_mood = None
biometric_history = deque(maxlen=10)  # Store last 10 readings for averaging
favorites_file = "favorites.json"

# Load favorites from file
def load_favorites():
    try:
        if os.path.exists(favorites_file):
            with open(favorites_file, 'r') as f:
                return json.load(f)
        return []
    except:
        return []

# Save favorites to file
def save_favorites(favorites):
    try:
        with open(favorites_file, 'w') as f:
            json.dump(favorites, f, indent=2)
    except Exception as e:
        print(f"Error saving favorites: {e}")

favorites = load_favorites()

def get_music_for_mood(mood_tag):
    """Fetch multiple tracks for a given mood tag."""
    try:
        lfm_url = f"https://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={mood_tag}&api_key={LASTFM_API_KEY}&format=json&limit=10"
        lfm_response = requests.get(lfm_url, timeout=5)
        lfm_data = lfm_response.json()
        
        if 'tracks' not in lfm_data or 'track' not in lfm_data['tracks']:
            return []
        
        tracks = []
        for track_data in lfm_data['tracks']['track'][:6]:
            track_name = track_data.get('name', '')
            artist_name = track_data.get('artist', {}).get('name', '')
            
            query = f"{track_name} {artist_name}"
            itunes_url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
            
            try:
                itunes_response = requests.get(itunes_url, timeout=5)
                itunes_data = itunes_response.json()
                
                if itunes_data.get('results'):
                    result = itunes_data['results'][0]
                    tracks.append({
                        'name': track_name,
                        'artist': artist_name,
                        'previewUrl': result.get('previewUrl', ''),
                        'artwork': result.get('artworkUrl100', '').replace('100x100', '600x600'),
                        'duration': 30,
                        'mood': mood_tag
                    })
            except Exception as e:
                print(f"iTunes API error for {track_name}: {e}")
                continue
        
        return tracks
    
    except Exception as e:
        print(f"Music fetch error: {e}")
        return []

def determine_mood_from_average():
    """Determine mood based on average of recent biometric readings."""
    if not biometric_history:
        return "deep_focus", random.choice(FocusTags["deep_focus"])
    
    # Calculate averages
    avg_hr = sum(reading['hr'] for reading in biometric_history) / len(biometric_history)
    avg_blinks = sum(reading['blinks'] for reading in biometric_history) / len(biometric_history)
    
    print(f"📊 Average metrics - HR: {avg_hr:.1f} BPM, Blinks/min: {avg_blinks:.1f}")
    
    # Determine mood category based on averages
    if avg_hr > 95 or avg_blinks > 20:
        category = "high_stress"
    elif 12 <= avg_blinks <= 20 and 50 <= avg_hr <= 95:
        category = "deep_focus"
    elif avg_hr < 50 and avg_blinks < 12:
        category = "low_energy"
    else:
        category = "deep_focus"
    
    mood_tag = random.choice(FocusTags[category])
    return category, mood_tag

def biometric_monitoring_loop():
    """Main loop that monitors biometrics and collects data for averaging."""
    global monitoring_active, current_mood, bio_monitor, biometric_history
    
    print("Biometric monitoring loop started")
    song_start_time = None
    last_music_change = time.time()
    
    while monitoring_active:
        try:
            # Get current biometric data
            hr, blinks_per_min = bio_monitor.get_metrics()
            blink_count = bio_monitor.get_blink_count()
            
            # Store reading for averaging
            biometric_history.append({
                'hr': hr,
                'blinks': blinks_per_min,
                'timestamp': time.time()
            })
            
            # Emit biometric update to frontend
            socketio.emit('biometric_update', {
                'heart_rate': round(hr, 1),
                'blinks_per_minute': round(blinks_per_min, 1),
                'blink_count': blink_count,
                'avg_heart_rate': round(sum(r['hr'] for r in biometric_history) / len(biometric_history), 1) if biometric_history else 0,
                'avg_blinks': round(sum(r['blinks'] for r in biometric_history) / len(biometric_history), 1) if biometric_history else 0
            })
            
            # Check if song has finished (30 seconds for iTunes preview)
            current_time = time.time()
            time_since_last_change = current_time - last_music_change
            
            # Only change music after song completes (30 seconds + 2 second buffer)
            if time_since_last_change >= (SONG_DURATION + 2):
                # Determine new mood based on averages
                mood_category, mood_tag = determine_mood_from_average()
                
                print(f"🎵 Song completed. Switching to {mood_category} based on average biometrics")
                
                # Fetch tracks for this mood
                tracks = get_music_for_mood(mood_tag)
                
                if tracks:
                    socketio.emit('music_update', {
                        'mood': mood_category,
                        'mood_tag': mood_tag,
                        'tracks': tracks
                    })
                    socketio.emit('mood_change', {
                        'mood': mood_category,
                        'reason': f"Avg HR: {sum(r['hr'] for r in biometric_history) / len(biometric_history):.1f} BPM, Avg Blinks: {sum(r['blinks'] for r in biometric_history) / len(biometric_history):.1f}/min"
                    })
                    
                    current_mood = mood_category
                    last_music_change = current_time
                    # Clear history for next song cycle
                    biometric_history.clear()
            
            time.sleep(2)  # Check every 2 seconds
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(1)
    
    print("Biometric monitoring loop stopped")

@app.route('/')
def index():
    return "Biometric Music Player Backend Running"

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """Get all favorite tracks"""
    return jsonify(favorites)

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    """Add a track to favorites"""
    global favorites
    track = request.json
    
    # Check if already in favorites
    if not any(f['name'] == track['name'] and f['artist'] == track['artist'] for f in favorites):
        favorites.append(track)
        save_favorites(favorites)
        socketio.emit('favorites_updated', favorites)
        return jsonify({'success': True, 'favorites': favorites})
    
    return jsonify({'success': False, 'message': 'Already in favorites'})

@app.route('/api/favorites/<int:index>', methods=['DELETE'])
def remove_favorite(index):
    """Remove a track from favorites"""
    global favorites
    
    if 0 <= index < len(favorites):
        removed = favorites.pop(index)
        save_favorites(favorites)
        socketio.emit('favorites_updated', favorites)
        return jsonify({'success': True, 'removed': removed, 'favorites': favorites})
    
    return jsonify({'success': False, 'message': 'Invalid index'})

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'status': 'connected'})
    emit('favorites_updated', favorites)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_monitoring')
def handle_start_monitoring():
    global monitoring_active, bio_monitor, current_mood, biometric_history
    
    if not monitoring_active:
        print("Starting biometric monitoring...")
        
        bio_monitor = BiometricsMonitor(show_ui=False)
        bio_monitor.start()
        
        monitoring_active = True
        current_mood = None
        biometric_history.clear()
        
        thread = threading.Thread(target=biometric_monitoring_loop, daemon=True)
        thread.start()
        
        emit('monitoring_status', {'status': 'started'})
        
        # Wait for initial data
        time.sleep(2)
        hr, bpm = bio_monitor.get_metrics()
        mood_category, mood_tag = determine_mood_from_average() if biometric_history else ("deep_focus", random.choice(FocusTags["deep_focus"]))
        current_mood = mood_category
        
        tracks = get_music_for_mood(mood_tag)
        if tracks:
            emit('music_update', {
                'mood': mood_category,
                'mood_tag': mood_tag,
                'tracks': tracks
            })

@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    global monitoring_active, bio_monitor
    
    monitoring_active = False
    if bio_monitor:
        bio_monitor.stop()
        bio_monitor = None
    
    emit('monitoring_status', {'status': 'stopped'})

@socketio.on('request_more_music')
def handle_request_more_music(data):
    """Fetch more songs for current mood when queue runs low"""
    mood_category = data.get('mood', current_mood or 'deep_focus')
    mood_tag = random.choice(FocusTags.get(mood_category, FocusTags['deep_focus']))
    
    print(f"📥 Fetching more songs for {mood_category} mood...")
    tracks = get_music_for_mood(mood_tag)
    
    if tracks:
        emit('more_music_loaded', {
            'mood': mood_category,
            'tracks': tracks
        })
    else:
        print(f"❌ No additional tracks found for {mood_category}")

@socketio.on('queue_low')
def handle_queue_low(data):
    """Automatically fetch more songs when queue is running low"""
    mood_category = data.get('mood', current_mood or 'deep_focus')
    print(f"⚠️ Queue running low! Auto-fetching more {mood_category} songs...")
    
    mood_tag = random.choice(FocusTags.get(mood_category, FocusTags['deep_focus']))
    tracks = get_music_for_mood(mood_tag)
    
    if tracks:
        emit('more_music_loaded', {
            'mood': mood_category,
            'tracks': tracks,
            'auto': True
        })

@socketio.on('add_to_favorites')
def handle_add_favorite(track):
    """Add track to favorites via WebSocket"""
    global favorites
    
    if not any(f['name'] == track['name'] and f['artist'] == track['artist'] for f in favorites):
        favorites.append(track)
        save_favorites(favorites)
        emit('favorites_updated', favorites, broadcast=True)
        emit('favorite_added', {'success': True})
    else:
        emit('favorite_added', {'success': False, 'message': 'Already in favorites'})

@socketio.on('remove_from_favorites')
def handle_remove_favorite(data):
    """Remove track from favorites via WebSocket"""
    global favorites
    
    track_name = data.get('name')
    track_artist = data.get('artist')
    
    favorites = [f for f in favorites if not (f['name'] == track_name and f['artist'] == track_artist)]
    save_favorites(favorites)
    emit('favorites_updated', favorites, broadcast=True)
    emit('favorite_removed', {'success': True})

if __name__ == '__main__':
    print("=" * 60)
    print("🎵 Biometric Music Player Backend")
    print("=" * 60)
    print("✅ Make sure your webcam is connected!")
    print("✅ Make sure biometrics.py is in the same folder!")
    print("✅ Backend running on http://localhost:5000")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)