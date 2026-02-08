# 🎯 Focus Buddy

**AI-Powered Biometric Music Player for Enhanced Productivity**

Focus Buddy is an intelligent music player that monitors your biometric data in real-time and automatically adapts the music to match your mental state. Using your webcam to track heart rate and blink patterns, it creates the perfect soundtrack for work, study, or relaxation.

![Focus Buddy](https://img.shields.io/badge/Version-1.0.0-purple) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![React](https://img.shields.io/badge/React-18-61dafb) ![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### 🎵 **Smart Music Selection**
- **Automatic mood detection** based on heart rate and blink patterns
- **Three mood categories:**
  - ⚡ **Energy Boost** - Upbeat music when you're tired (HR < 65, Blinks < 12)
  - 🎯 **Deep Focus** - Instrumental music for concentration (HR 60-90, Blinks 12-20)
  - 🌿 **Calm & Relax** - Soothing music when stressed (HR > 90, Blinks > 20)
- **Song completion guarantee** - Never interrupts mid-song
- **Infinite queue** - Automatically loads more songs as needed

### 📊 **Real-Time Biometric Monitoring**
- **Heart rate detection** using remote photoplethysmography (rPPG)
- **Blink rate tracking** via facial landmark detection
- **Average calculations** for stable mood detection
- **Live dashboard** with visual indicators

### 🎛️ **Advanced Playback Controls**
- ⏮ **Previous button** with 20-song history
- ⏯ **Play/Pause** control
- ⏭ **Next/Skip** with auto-queue refill
- 🔀 **Shuffle mode**
- 🔁 **Repeat modes** (off/one/all)
- 🔊 **Volume slider** with mute
- ⏩ **Seekable progress bar** - Click to jump anywhere

### 💾 **Favorites & History**
- ❤️ **Save favorite songs** with persistent storage
- 📜 **Listening history** (last 50 songs)
- 🎨 **Beautiful UI** with glassmorphic design
- 🎨 **Mood-based themes** that match your current state

### 🤖 **Manual Override**
- **Manual mood selector** to override auto-detection
- Switch between Auto/Energy Boost/Deep Focus/Calm modes
- Perfect for when you want specific vibes

---

## 🖼️ Screenshots

**Main Player Interface**
- Real-time biometric monitoring on the left
- Large album artwork with playback controls
- Up Next queue showing 5 upcoming tracks
- Glassmorphic design with mood-based gradients

**Favorites Page**
- All your saved tracks in one place
- Quick play from favorites
- Easy management with delete option

**Listening History**
- View your recently played tracks
- Timestamps for each session
- Replay past songs instantly

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **Webcam** (required for biometric monitoring)
- **Last.fm API Key** ([Get one here](https://www.last.fm/api/account/create))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/focus-buddy.git
   cd focus-buddy
   ```

2. **Set up Python backend**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate it
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure API key**
   
   Create a `.env` file in the project root:
   ```env
   LASTFM_API_KEY=your_api_key_here
   ```

4. **Set up React frontend**
   ```bash
   # Create src folder
   mkdir src
   
   # Move React files (or they might already be there)
   # Windows:
   move *.jsx src\
   move index.css src\
   
   # Mac/Linux:
   mv *.jsx src/
   mv index.css src/
   
   # Install dependencies
   npm install
   ```

5. **Run the application**
   
   Open **two terminals**:
   
   **Terminal 1 - Backend:**
   ```bash
   python backend.py
   ```
   
   **Terminal 2 - Frontend:**
   ```bash
   npm run dev
   ```

6. **Open in browser**
   ```
   http://localhost:3000
   ```

7. **Allow webcam access** when prompted and click **"Start Monitoring"**!

---

## 📁 Project Structure

```
focus-buddy/
├── src/                          # React frontend source
│   ├── BiometricMusicPlayer.jsx  # Main React component
│   ├── App.jsx                   # App wrapper
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Tailwind styles
├── biometrics.py                 # Biometric monitoring module
├── backend.py                    # Flask-SocketIO server
├── .env                          # API keys (create this!)
├── index.html                    # HTML entry
├── package.json                  # Node dependencies
├── requirements.txt              # Python dependencies
├── vite.config.js                # Vite configuration
├── tailwind.config.js            # Tailwind setup
├── postcss.config.js             # PostCSS config
├── favorites.json                # Saved favorites (auto-created)
└── README.md                     # You are here!
```

---

## 🔧 How It Works

### Architecture

```
┌─────────────┐
│   Webcam    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  biometrics.py          │
│  • MediaPipe Face Mesh  │
│  • Custom rPPG (HR)     │
│  • Blink Detection      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│  backend.py (Flask)     │
│  • Mood Detection       │
│  • Music API Calls      │
│  • WebSocket Server     │
└──────┬──────────────────┘
       │ WebSocket
       ▼
┌─────────────────────────┐
│  React Frontend         │
│  • Music Player UI      │
│  • Queue Management     │
│  • Favorites System     │
└─────────────────────────┘
```

### Biometric Detection

**Heart Rate (rPPG):**
1. Extracts green channel from face region
2. Applies FFT to detect periodic blood flow changes
3. Converts frequency to BPM (45-180 range)
4. Requires 15-20 seconds for accurate reading

**Blink Detection:**
1. Uses MediaPipe face mesh (468 facial landmarks)
2. Calculates Eye Aspect Ratio (EAR) from eye landmarks
3. Detects blinks when EAR < 0.012
4. Tracks blinks per minute for mood assessment

### Mood Detection Logic

```python
if avg_hr > 90 or avg_blinks > 20:
    → High Stress → Calm music
    
elif avg_hr < 65 and avg_blinks < 12:
    → Low Energy → Upbeat music
    
elif 60 <= avg_hr <= 90 and 12 <= avg_blinks <= 20:
    → Deep Focus → Instrumental music
```

### Music Flow

1. **Queue Management:**
   - Frontend maintains 3-6 song queue
   - Auto-refills when queue < 3 songs
   - Prevents interruptions

2. **Song Transitions:**
   - Songs always play to completion (30s)
   - Mood changes queued for next song
   - Smooth auto-play between tracks

3. **API Integration:**
   - Last.fm API for track metadata
   - iTunes API for 30-second previews
   - Caches favorites locally

---

## 🎨 Customization

### Adjust Mood Thresholds

Edit `backend.py` (around line 110):

```python
def determine_mood_from_average():
    # High Stress
    if avg_hr > 90 or avg_blinks > 20:  # ← Adjust these
        category = "high_stress"
    
    # Low Energy  
    elif avg_hr < 65 and avg_blinks < 12:  # ← Adjust these
        category = "low_energy"
    
    # Deep Focus
    elif 12 <= avg_blinks <= 20 and 60 <= avg_hr <= 90:  # ← Adjust these
        category = "deep_focus"
```

### Change Music Tags

Edit `backend.py` (line 18):

```python
FocusTags = {
    "low_energy": ["upbeat", "electro", "motivation", "energetic", "dance"],
    "deep_focus": ["alphawaves", "instrumental", "focus", "ambient"],
    "high_stress": ["chillout", "relax", "calm", "meditation"],
}
```

### Customize UI Colors

Edit `BiometricMusicPlayer.jsx` (line 5):

```jsx
const MOOD_CONFIG = {
  low_energy: {
    name: "Energy Boost",
    gradient: "from-orange-500 to-pink-500",  // ← Change gradient
    icon: "⚡",
    color: "#FF6B35"
  },
  // ... customize other moods
};
```

---

## 🐛 Troubleshooting

### Backend Issues

**"Could not open camera"**
- Check webcam permissions
- Ensure no other app is using the camera
- Try different camera index: `BiometricsMonitor(camera_index=1)`

**"ModuleNotFoundError: No module named 'biometrics'"**
- Make sure `biometrics.py` is in the same folder as `backend.py`
- Check virtual environment is activated

**Heart rate shows 0**
- Give it 15-20 seconds to calibrate
- Ensure good lighting on your face
- Stay relatively still
- Check backend terminal for "No face detected"

### Frontend Issues

**"Backend not connected"**
- Verify `backend.py` is running
- Check port 5000 is not in use
- Look for errors in backend terminal

**No music playing**
- Verify Last.fm API key in `.env`
- Check internet connection
- Some tracks may not have iTunes previews

**Songs change too fast**
- This is fixed in the latest version!
- Make sure you have the updated `backend.py`

### API Issues

**Last.fm API errors**
- Check API key is correct
- Verify `.env` file is in project root
- Check API rate limits (50 req/sec)

---

## 📊 Technical Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **Flask-SocketIO** - WebSocket communication
- **Flask-CORS** - Cross-origin support
- **OpenCV** - Computer vision
- **MediaPipe** - Face mesh detection
- **NumPy** - Numerical processing
- **SciPy** - Signal processing for rPPG

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Socket.io Client** - WebSocket client

### APIs
- **Last.fm API** - Music metadata
- **iTunes Search API** - 30-second previews

---

## 🎯 Features Roadmap

### Completed ✅
- [x] Real-time biometric monitoring
- [x] Automatic mood detection
- [x] Smart music selection
- [x] Favorites system
- [x] Listening history
- [x] Manual mood override
- [x] Volume controls
- [x] Shuffle & repeat
- [x] Infinite queue
- [x] Song completion guarantee
- [x] Seekable progress bar

### Coming Soon 🚀
- [ ] Pomodoro timer integration
- [ ] Daily analytics dashboard
- [ ] Custom playlists
- [ ] Export to Spotify
- [ ] Multiple user profiles
- [ ] Mobile app version
- [ ] Posture detection
- [ ] Break reminders
- [ ] Focus score calculation
- [ ] Weekly reports

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt  # If you create this
npm install --save-dev

# Run tests
pytest  # For Python
npm test  # For React
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👏 Acknowledgments

- **MediaPipe** by Google for face mesh technology
- **Last.fm** for music metadata API
- **Apple iTunes** for music previews
- **React** and **Tailwind CSS** communities
- All the open-source contributors who made this possible

---


## ⭐ Show Your Support

If Focus Buddy helps you stay focused and productive, give it a ⭐ on GitHub!

---

**Made with ❤️**

*Stay focused, stay productive!* 🎯🎵
