# 🚀 Complete Setup Guide - Biometric Music Player

## 📁 Project Structure

Your project folder should look like this:

```
Mac-A-Thon/
├── src/                           
│   ├── BiometricMusicPlayer.jsx   ← React UI component
│   ├── App.jsx                    ← React app wrapper
│   ├── main.jsx                   ← React entry point
│   └── index.css                  ← Tailwind CSS
├── biometrics.py                  ← Your existing biometrics monitor
├── backend.py                     ← NEW Flask-SocketIO server
├── .env                           ← Your API key
├── index.html                     ← HTML entry
├── package.json                   ← Node dependencies
├── requirements.txt               ← Python dependencies
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## ⚙️ Step 1: File Organization

### 1.1 Create `src` folder
```bash
mkdir src
```

### 1.2 Move React files to src
```bash
move BiometricMusicPlayer.jsx src\
move App.jsx src\
move main.jsx src\
move index.css src\
```

### 1.3 Keep these files in ROOT:
- ✅ `backend.py` (new Flask server)
- ✅ `biometrics.py` (your existing file)
- ✅ `index.html`
- ✅ `package.json`
- ✅ `requirements.txt`
- ✅ All `.js` config files

## 🐍 Step 2: Python Backend Setup

### 2.1 Create/Update .env file

Create a file called `.env` in your project root:

```
LASTFM_API_KEY=your_api_key_here
```

### 2.2 Install Python Dependencies

```bash
# Activate virtual environment (if not already active)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## ⚛️ Step 3: React Frontend Setup

### 3.1 Install Node Dependencies

```bash
npm install
```

This will install:
- React & React DOM
- Vite (build tool)
- Tailwind CSS
- Framer Motion (animations)
- Socket.io Client (WebSocket)

## 🎮 Step 4: Running the Application

### 4.1 Start Backend (Terminal 1)

```bash
# Make sure you're in the project folder
cd Mac-A-Thon

# Activate virtual environment
venv\Scripts\activate

# Run backend
python backend.py
```

You should see:
```
====================================================
🎵 Biometric Music Player Backend
====================================================
✅ Make sure your webcam is connected!
✅ Make sure biometrics.py is in the same folder!
✅ Backend running on http://localhost:5000
====================================================
```

**Keep this terminal running!**

### 4.2 Start Frontend (Terminal 2)

Open a NEW PowerShell terminal:

```bash
cd Mac-A-Thon
npm run dev
```

You should see:
```
VITE v5.0.0  ready in 500 ms
➜  Local:   http://localhost:3000/
```

### 4.3 Open in Browser

1. Go to: **http://localhost:3000**
2. Allow webcam access when prompted
3. Click **"Start Monitoring"** button
4. Music will start playing based on your biometrics!

## 🎵 How It Works

### Data Flow:

```
Webcam → biometrics.py (your existing code)
    ↓
backend.py (Flask-SocketIO)
    ↓
WebSocket → React UI (BiometricMusicPlayer.jsx)
    ↓
Audio Player
```

### Mood Detection:

| Condition | Mood | Music Type |
|-----------|------|------------|
| HR > 95 or Blinks/min > 20 | 😰 High Stress | Calm, relaxing |
| HR 50-95 & Blinks 12-20 | 🎯 Deep Focus | Instrumental, focus |
| HR < 50 or Blinks < 12 | ⚡ Low Energy | Upbeat, energetic |

### Features:

✅ **Real-time biometric monitoring** (heart rate & blink rate)
✅ **Automatic mood detection** based on your state
✅ **Dynamic music selection** from Last.fm + iTunes
✅ **Beautiful Spotify-like UI** with animations
✅ **Queue management** (shows next 5 tracks)
✅ **Manual controls** (play/pause, skip, select track)

## 🐛 Troubleshooting

### Issue: "Cannot find module 'biometrics'"

**Solution:** Make sure `biometrics.py` is in the same folder as `backend.py`

### Issue: "ModuleNotFoundError: No module named 'yarppg'"

**Solution:** 
Your `biometrics.py` uses `yarppg`. Install it:
```bash
pip install git+https://github.com/RemoteHeart/yarppg.git
```

Or if that doesn't work:
```bash
pip install opencv-python mediapipe numpy scipy
```

Then manually download yarppg from GitHub.

### Issue: "Backend not connected"

**Solution:**
1. Check if `backend.py` is running in Terminal 1
2. Make sure port 5000 is not used by another app
3. Look for errors in the backend terminal

### Issue: "No music playing"

**Solution:**
1. Check your `.env` file has the correct Last.fm API key
2. Verify internet connection
3. Check backend terminal for API errors

### Issue: "Heart rate shows 0"

**Solution:**
1. Give it 15-20 seconds to calibrate
2. Ensure good lighting on your face
3. Stay relatively still
4. Check backend terminal for "No face detected" warnings

### Issue: Files in wrong location

**Solution:**
Run this in PowerShell:
```bash
# Create src folder
mkdir src -Force

# Move React files
Get-ChildItem -Filter "*.jsx" | Move-Item -Destination "src\"
Get-ChildItem -Filter "index.css" | Move-Item -Destination "src\"
```

## 📝 Key Differences from Your Original Code

### Your `music.py` code:
- ✅ Used `BiometricsMonitor` class
- ✅ VLC player for audio
- ✅ Terminal-based UI

### New `backend.py`:
- ✅ Still uses your `BiometricsMonitor` class
- ✅ Adds Flask-SocketIO for web communication
- ✅ Sends data to React UI via WebSocket
- ✅ No VLC needed (browser plays audio)

### What Stayed the Same:
- ✅ Your `biometrics.py` file (no changes needed!)
- ✅ Same mood detection logic
- ✅ Same Last.fm + iTunes API integration
- ✅ Same biometric monitoring approach

## 🎨 Customization

### Change Mood Thresholds

Edit `backend.py` around line 75:

```python
def determine_mood(hr, blinks_per_min):
    if hr > 95 or blinks_per_min > 20:  # Adjust these values
        category = "high_stress"
    # ...
```

### Change Music Tags

Edit `backend.py` around line 18:

```python
FocusTags = {
    "low_energy": ["upbeat", "dance", "edm"],  # Your custom tags
    # ...
}
```

### Change UI Colors

Edit `BiometricMusicPlayer.jsx` around line 5:

```jsx
const MOOD_CONFIG = {
  low_energy: {
    gradient: "from-yellow-500 to-orange-500",  # Custom colors
    // ...
```

## 🚀 Next Steps

Once it's working:

1. ✅ Test with different lighting conditions
2. ✅ Adjust thresholds for your personal biometrics
3. ✅ Add more mood categories
4. ✅ Integrate Spotify API for full tracks
5. ✅ Save user preferences

---

## 📚 Quick Commands Reference

```bash
# Start backend
python backend.py

# Start frontend
npm run dev

# Install Python package
pip install package-name

# Install Node package  
npm install package-name

# Clean Node modules
rm -rf node_modules package-lock.json
npm install
```

---

🎉 **That's it! You now have a beautiful web-based biometric music player using your existing Python code!**
