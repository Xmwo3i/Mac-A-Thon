import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import io from 'socket.io-client';

const MOOD_CONFIG = {
  low_energy: {
    name: "Energy Boost",
    gradient: "from-orange-500 to-pink-500",
    icon: "⚡",
    color: "#FF6B35"
  },
  deep_focus: {
    name: "Deep Focus",
    gradient: "from-cyan-500 to-blue-500",
    icon: "🎯",
    color: "#4ECDC4"
  },
  high_stress: {
    name: "Calm & Relax",
    gradient: "from-green-400 to-teal-400",
    icon: "🌿",
    color: "#95E1D3"
  }
};

const BiometricMusicPlayer = () => {
  // Navigation
  const [currentPage, setCurrentPage] = useState('player');
  
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [isMonitoring, setIsMonitoring] = useState(false);
  
  // Biometric state
  const [heartRate, setHeartRate] = useState(0);
  const [blinksPerMinute, setBlinksPerMinute] = useState(0);
  const [blinkCount, setBlinkCount] = useState(0);
  const [avgHeartRate, setAvgHeartRate] = useState(0);
  const [avgBlinks, setAvgBlinks] = useState(0);
  
  // Music state
  const [currentMood, setCurrentMood] = useState('deep_focus');
  const [manualMood, setManualMood] = useState(null); // Manual override
  const [currentTrack, setCurrentTrack] = useState(null);
  const [nextTracks, setNextTracks] = useState([]);
  const [previousTracks, setPreviousTracks] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(30);
  const [volume, setVolume] = useState(0.7);
  const [isMuted, setIsMuted] = useState(false);
  const [repeatMode, setRepeatMode] = useState('off'); // 'off', 'one', 'all'
  const [shuffleMode, setShuffleMode] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  
  // Favorites & History
  const [favorites, setFavorites] = useState([]);
  const [listeningHistory, setListeningHistory] = useState([]);
  
  // Refs
  const audioRef = useRef(null);
  const socketRef = useRef(null);
  const queueFetchTimeoutRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    console.log('Initializing socket connection...');
    
    socketRef.current = io('http://localhost:5000', {
      transports: ['polling', 'websocket'],
      reconnection: true
    });

    socketRef.current.on('connect', () => {
      console.log('✅ Connected to backend');
      setIsConnected(true);
    });

    socketRef.current.on('disconnect', () => {
      console.log('❌ Disconnected');
      setIsConnected(false);
      setIsMonitoring(false);
    });

    socketRef.current.on('biometric_update', (data) => {
      setHeartRate(data.heart_rate || 0);
      setBlinksPerMinute(data.blinks_per_minute || 0);
      setBlinkCount(data.blink_count || 0);
      setAvgHeartRate(data.avg_heart_rate || 0);
      setAvgBlinks(data.avg_blinks || 0);
    });

    socketRef.current.on('music_update', (data) => {
      console.log('🎵 Music update:', data);
      
      // Only accept music_update for initial load or when queue is empty
      if (!data.initial && currentTrack && currentTrack.id !== 'loading' && nextTracks.length > 0) {
        console.log('⏸ Ignoring music_update - using existing queue');
        return;
      }
      
      if (data.tracks && data.tracks.length > 0) {
        const validTracks = data.tracks
          .filter(t => t.previewUrl)
          .map((track, index) => ({
            ...track,
            id: `${track.name}-${track.artist}-${index}-${Date.now()}`
          }));
        
        if (validTracks.length > 0) {
          setCurrentMood(data.mood);
          setCurrentTrack(validTracks[0]);
          setNextTracks(validTracks.slice(1, 6));
          playTrack(validTracks[0]);
        }
      }
    });

    socketRef.current.on('more_music_loaded', (data) => {
      console.log('📥 More music loaded:', data);
      setIsLoadingMore(false);
      
      if (data.tracks && data.tracks.length > 0) {
        const validTracks = data.tracks
          .filter(t => t.previewUrl)
          .map((track, index) => ({
            ...track,
            id: `${track.name}-${track.artist}-${index}-${Date.now()}`
          }));
        
        // If current track is loading placeholder, replace it
        if (currentTrack?.id === 'loading' && validTracks.length > 0) {
          setCurrentTrack(validTracks[0]);
          setNextTracks(validTracks.slice(1));
          playTrack(validTracks[0]);
        } else {
          // Add to end of queue
          setNextTracks(prev => {
            // Remove duplicates
            const newTracks = validTracks.filter(newTrack => 
              !prev.some(existing => existing.name === newTrack.name && existing.artist === newTrack.artist)
            );
            return [...prev, ...newTracks];
          });
        }
        
        if (data.auto) {
          console.log('✅ Queue automatically refilled!');
        }
      }
    });

    socketRef.current.on('monitoring_status', (data) => {
      setIsMonitoring(data.status === 'started');
    });

    socketRef.current.on('favorites_updated', (data) => {
      setFavorites(data);
    });

    socketRef.current.on('mood_change', (data) => {
      console.log('😊 Mood changed:', data);
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  // Volume control
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
      audioRef.current.muted = isMuted;
    }
  }, [volume, isMuted]);

  const handleSeek = (e) => {
    if (!audioRef.current || !audioRef.current.duration) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * audioRef.current.duration;
    
    audioRef.current.currentTime = newTime;
    setProgress(percentage * 100);
  };

  const toggleMonitoring = () => {
    if (!socketRef.current?.connected) {
      alert('Not connected to backend');
      return;
    }

    if (isMonitoring) {
      socketRef.current.emit('stop_monitoring');
    } else {
      socketRef.current.emit('start_monitoring');
    }
  };

  const requestMoreMusic = (mood) => {
    if (isLoadingMore) return; // Prevent multiple simultaneous requests
    
    setIsLoadingMore(true);
    console.log('📡 Requesting more music for mood:', mood);
    
    if (socketRef.current) {
      socketRef.current.emit('queue_low', { mood: mood || currentMood });
    }
    
    // Timeout to reset loading state if request fails
    if (queueFetchTimeoutRef.current) {
      clearTimeout(queueFetchTimeoutRef.current);
    }
    queueFetchTimeoutRef.current = setTimeout(() => {
      setIsLoadingMore(false);
    }, 5000);
  };

  const playTrack = (track, addToHistory = true) => {
    console.log('🎵 Playing:', track.name);
    if (audioRef.current && track?.previewUrl) {
      // Save current track to history
      if (addToHistory && currentTrack && currentTrack.id !== 'loading') {
        setPreviousTracks(prev => [currentTrack, ...prev].slice(0, 20));
        setListeningHistory(prev => [{
          ...currentTrack,
          playedAt: new Date().toISOString()
        }, ...prev].slice(0, 50));
      }
      
      audioRef.current.src = track.previewUrl;
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(error => {
          console.error('Playback failed:', error);
          setIsPlaying(false);
        });
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current && currentTrack?.id !== 'loading') {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play()
          .then(() => setIsPlaying(true))
          .catch(error => console.error('Playback failed:', error));
      }
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  const skipTrack = () => {
    // Check if we need to fetch more songs BEFORE we skip
    if (nextTracks.length <= 2) {
      console.log('⚠️ Queue getting low, fetching more...');
      requestMoreMusic(manualMood || currentMood);
    }
    
    if (nextTracks.length > 0) {
      const nextTrack = nextTracks[0];
      setCurrentTrack(nextTrack);
      setNextTracks(prev => prev.slice(1));
      playTrack(nextTrack);
    } else if (!isLoadingMore) {
      // Queue is completely empty and not already loading
      console.log('❌ Queue empty! Fetching songs immediately...');
      requestMoreMusic(manualMood || currentMood);
      
      // Show loading placeholder
      setCurrentTrack({
        id: 'loading',
        name: 'Loading more songs...',
        artist: 'Please wait',
        previewUrl: null,
        artwork: null
      });
      setIsPlaying(false);
    }
  };

  const previousTrack = () => {
    if (previousTracks.length > 0) {
      const prevTrack = previousTracks[0];
      if (currentTrack && currentTrack.id !== 'loading') {
        setNextTracks(prev => [currentTrack, ...prev]);
      }
      setPreviousTracks(prev => prev.slice(1));
      setCurrentTrack(prevTrack);
      playTrack(prevTrack, false);
    }
  };

  const selectTrack = (track) => {
    setCurrentTrack(track);
    setNextTracks(prev => prev.filter(t => t.id !== track.id));
    playTrack(track);
  };

  const toggleRepeat = () => {
    const modes = ['off', 'all', 'one'];
    const currentIndex = modes.indexOf(repeatMode);
    setRepeatMode(modes[(currentIndex + 1) % modes.length]);
  };

  const toggleShuffle = () => {
    if (!shuffleMode && nextTracks.length > 0) {
      // Shuffle the queue
      const shuffled = [...nextTracks].sort(() => Math.random() - 0.5);
      setNextTracks(shuffled);
    }
    setShuffleMode(!shuffleMode);
  };

  const changeMoodManually = (mood) => {
    setManualMood(mood);
    setCurrentMood(mood);
    
    if (socketRef.current) {
      socketRef.current.emit('queue_low', { mood });
    }
  };

  const addToFavorites = (track) => {
    if (socketRef.current && track && track.id !== 'loading') {
      socketRef.current.emit('add_to_favorites', {
        name: track.name,
        artist: track.artist,
        previewUrl: track.previewUrl,
        artwork: track.artwork,
        duration: track.duration,
        mood: track.mood || currentMood
      });
    }
  };

  const removeFromFavorites = (track) => {
    if (socketRef.current) {
      socketRef.current.emit('remove_from_favorites', {
        name: track.name,
        artist: track.artist
      });
    }
  };

  const isInFavorites = (track) => {
    if (!track) return false;
    return favorites.some(f => f.name === track.name && f.artist === track.artist);
  };

  // Update progress and handle song end
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateProgress = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        const currentProgress = (audio.currentTime / audio.duration) * 100;
        setProgress(currentProgress);
        setTimeRemaining(Math.ceil(audio.duration - audio.currentTime));
      }
    };

    const handleEnded = () => {
      console.log('🎵 Song ended');
      
      // Notify backend that song ended
      if (socketRef.current) {
        socketRef.current.emit('song_ended', {
          queue_length: nextTracks.length
        });
      }
      
      if (repeatMode === 'one' && currentTrack) {
        // Repeat current song
        audio.currentTime = 0;
        audio.play();
      } else if (nextTracks.length > 0) {
        // Auto-play next track from queue
        skipTrack();
      } else {
        // Queue empty - request more music for current mood
        console.log('📭 Queue empty at song end, requesting more...');
        if (socketRef.current) {
          socketRef.current.emit('queue_low', { mood: manualMood || currentMood });
        }
      }
    };

    audio.addEventListener('timeupdate', updateProgress);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', updateProgress);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [nextTracks, currentTrack, repeatMode, currentMood, manualMood]);

  const moodConfig = MOOD_CONFIG[currentMood] || MOOD_CONFIG.deep_focus;

  const getRepeatIcon = () => {
    if (repeatMode === 'one') return '🔂';
    if (repeatMode === 'all') return '🔁';
    return '↻';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@400;500;700&display=swap');
        * { font-family: 'DM Sans', sans-serif; }
        h1, h2, h3, .heading { font-family: 'Syne', sans-serif; }
        .glassmorphic {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .glow { box-shadow: 0 0 40px rgba(255, 255, 255, 0.1); }
        @keyframes pulse-ring {
          0%, 100% { transform: scale(1); opacity: 0.3; }
          50% { transform: scale(1.1); opacity: 0.1; }
        }
        .pulse-ring { animation: pulse-ring 2s ease-in-out infinite; }
        @keyframes rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .rotate-slow { animation: rotate 20s linear infinite; }
        
        /* Custom Dropdown Styling */
        .mood-selector {
          background: rgba(255, 255, 255, 0.08);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.15);
          color: white;
          padding: 0.5rem 2.5rem 0.5rem 1rem;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: all 0.3s ease;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='white' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 0.75rem center;
          background-size: 12px;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .mood-selector:hover {
          background: rgba(255, 255, 255, 0.12);
          border-color: rgba(255, 255, 255, 0.25);
          box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1);
        }
        
        .mood-selector:focus {
          outline: none;
          border-color: rgba(255, 255, 255, 0.3);
          box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
        }
        
        .mood-selector option {
          background: #1a1a2e;
          color: white;
          padding: 0.5rem;
        }
        
        .mood-selector option:hover {
          background: #2d2d44;
        }
      `}</style>

      <audio ref={audioRef} />

      {/* Navbar */}
      <nav className="glassmorphic border-b border-white/10">
        <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <h1 className="text-2xl font-bold text-white heading">🎵 FOCUS BUDDY</h1>
            
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage('player')}
                className={`px-4 py-2 rounded-lg transition-all text-sm ${
                  currentPage === 'player'
                    ? 'bg-white/20 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              >
                Player
              </button>
              <button
                onClick={() => setCurrentPage('favorites')}
                className={`px-4 py-2 rounded-lg transition-all text-sm flex items-center gap-2 ${
                  currentPage === 'favorites'
                    ? 'bg-white/20 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              >
                ❤️ Favorites ({favorites.length})
              </button>
              <button
                onClick={() => setCurrentPage('history')}
                className={`px-4 py-2 rounded-lg transition-all text-sm flex items-center gap-2 ${
                  currentPage === 'history'
                    ? 'bg-white/20 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              >
                📜 History ({listeningHistory.length})
              </button>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Manual Mood Selector */}
            <select
              value={manualMood || 'auto'}
              onChange={(e) => {
                const value = e.target.value;
                if (value === 'auto') {
                  setManualMood(null);
                } else {
                  changeMoodManually(value);
                }
              }}
              className="mood-selector text-sm font-medium"
            >
              <option value="auto">🤖 Auto Mood</option>
              <option value="low_energy">⚡ Energy Boost</option>
              <option value="deep_focus">🎯 Deep Focus</option>
              <option value="high_stress">🌿 Calm & Relax</option>
            </select>

            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
              <span className="text-sm text-gray-400">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            <button
              onClick={toggleMonitoring}
              disabled={!isConnected}
              className={`px-6 py-2 rounded-full font-medium transition-all text-sm ${
                isMonitoring
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-green-500 hover:bg-green-600'
              } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isMonitoring ? '⏹ Stop' : '▶ Start'} Monitoring
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="p-8">
        {currentPage === 'player' ? (
          /* Player Page */
          <div className="max-w-6xl mx-auto grid grid-cols-3 gap-6">
            {/* Biometric Panel */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              className="col-span-1 space-y-6"
            >
              {/* Heart Rate */}
              <div className="glassmorphic glow rounded-3xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-red-500 opacity-10 rounded-full blur-3xl"></div>
                <div className="relative z-10">
                  <div className="text-gray-400 text-sm font-medium mb-2">Heart Rate</div>
                  <div className="flex items-end gap-2">
                    <div className="text-5xl font-bold text-white heading">{heartRate.toFixed(0)}</div>
                    <div className="text-gray-400 text-lg mb-2">BPM</div>
                  </div>
                  <div className="mt-2 text-sm text-gray-500">Avg: {avgHeartRate.toFixed(0)} BPM</div>
                  
                  <div className="mt-4 relative w-16 h-16">
                    <div className="absolute inset-0 bg-red-500 rounded-full pulse-ring"></div>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-3xl">❤️</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Blinks */}
              <div className="glassmorphic glow rounded-3xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500 opacity-10 rounded-full blur-3xl"></div>
                <div className="relative z-10">
                  <div className="text-gray-400 text-sm font-medium mb-2">Blink Rate</div>
                  <div className="flex items-end gap-2">
                    <div className="text-5xl font-bold text-white heading">{blinksPerMinute.toFixed(1)}</div>
                    <div className="text-gray-400 text-lg mb-2">/min</div>
                  </div>
                  <div className="mt-2">
                    <div className="text-sm text-gray-500">Avg: {avgBlinks.toFixed(1)}/min</div>
                    <div className="text-sm text-gray-500">Total: {blinkCount} blinks</div>
                  </div>
                  <div className="mt-2 text-3xl">👁️</div>
                </div>
              </div>

              {/* Current Mood */}
              <div className={`glassmorphic glow rounded-3xl p-6 relative overflow-hidden bg-gradient-to-br ${moodConfig.gradient}`}>
                <div className="relative z-10">
                  <div className="text-white/80 text-sm font-medium mb-2">
                    {manualMood ? 'Manual Mode' : 'Current Mood'}
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-4xl">{moodConfig.icon}</div>
                    <div className="text-2xl font-bold text-white heading">{moodConfig.name}</div>
                  </div>
                  {timeRemaining > 0 && isMonitoring && !manualMood && (
                    <div className="mt-3 text-sm text-white/70">
                      Next mood check: {timeRemaining}s
                    </div>
                  )}
                  {isLoadingMore && (
                    <div className="mt-3 text-sm text-white/70">
                      Loading more songs...
                    </div>
                  )}
                </div>
              </div>

              {/* Queue Status */}
              <div className="glassmorphic glow rounded-2xl p-4">
                <div className="text-gray-400 text-xs font-medium mb-2">QUEUE STATUS</div>
                <div className="text-white text-sm">
                  {nextTracks.length} song{nextTracks.length !== 1 ? 's' : ''} in queue
                </div>
                {nextTracks.length <= 2 && (
                  <div className="text-yellow-400 text-xs mt-1">
                    ⚠️ Low queue - more songs loading
                  </div>
                )}
              </div>
            </motion.div>

            {/* Main Player */}
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="col-span-2 glassmorphic glow rounded-3xl p-8 relative overflow-hidden"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${moodConfig.gradient} opacity-20 blur-3xl`}></div>

              <div className="relative z-10">
                <AnimatePresence mode="wait">
                  {currentTrack ? (
                    <motion.div
                      key={currentTrack.id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className="flex gap-6 mb-8"
                    >
                      <div className="relative">
                        <div className="w-64 h-64 rounded-2xl overflow-hidden shadow-2xl">
                          {currentTrack.artwork ? (
                            <img
                              src={currentTrack.artwork}
                              alt={currentTrack.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className={`w-full h-full bg-gradient-to-br ${moodConfig.gradient} flex items-center justify-center text-6xl`}>
                              {currentTrack.id === 'loading' ? '⏳' : moodConfig.icon}
                            </div>
                          )}
                        </div>
                        
                        {isPlaying && currentTrack.id !== 'loading' && (
                          <div className="absolute -inset-4 border-4 border-white/20 rounded-2xl rotate-slow"></div>
                        )}
                      </div>

                      <div className="flex-1 flex flex-col justify-center">
                        <div className="text-gray-400 text-sm font-medium mb-2">NOW PLAYING</div>
                        <h2 className="text-4xl font-bold text-white mb-2 heading">{currentTrack.name}</h2>
                        <p className="text-2xl text-gray-300 mb-6">{currentTrack.artist}</p>

                        {/* Progress Bar */}
                        {currentTrack.id !== 'loading' && (
                          <>
                            <div className="mb-4">
                              <div 
                                className="h-2 bg-white/10 rounded-full overflow-hidden cursor-pointer hover:h-3 transition-all"
                                onClick={handleSeek}
                                title="Click to seek"
                              >
                                <motion.div
                                  className={`h-full bg-gradient-to-r ${moodConfig.gradient}`}
                                  style={{ width: `${progress}%` }}
                                ></motion.div>
                              </div>
                              <div className="flex justify-between text-sm text-gray-400 mt-2">
                                <span>{Math.floor((30 - timeRemaining) / 60)}:{String(Math.floor((30 - timeRemaining) % 60)).padStart(2, '0')}</span>
                                <span>0:30</span>
                              </div>
                            </div>

                            {/* Volume Control */}
                            <div className="mb-4 flex items-center gap-3">
                              <button
                                onClick={toggleMute}
                                className="text-gray-400 hover:text-white transition-colors text-xl"
                              >
                                {isMuted ? '🔇' : volume > 0.5 ? '🔊' : '🔉'}
                              </button>
                              <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.01"
                                value={isMuted ? 0 : volume}
                                onChange={(e) => {
                                  const newVolume = parseFloat(e.target.value);
                                  setVolume(newVolume);
                                  if (newVolume > 0 && isMuted) {
                                    setIsMuted(false);
                                  }
                                }}
                                className="flex-1 h-2 rounded-full appearance-none cursor-pointer"
                                style={{
                                  background: `linear-gradient(to right, ${moodConfig.color} 0%, ${moodConfig.color} ${(isMuted ? 0 : volume) * 100}%, rgba(255,255,255,0.1) ${(isMuted ? 0 : volume) * 100}%, rgba(255,255,255,0.1) 100%)`
                                }}
                              />
                              <span className="text-gray-400 text-sm w-10">{isMuted ? 0 : Math.round(volume * 100)}%</span>
                            </div>

                            {/* Controls */}
                            <div className="flex items-center gap-3">
                              <button
                                onClick={toggleShuffle}
                                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                                  shuffleMode ? 'bg-green-500 text-white' : 'bg-white/10 text-gray-400 hover:text-white'
                                }`}
                                title="Shuffle"
                              >
                                🔀
                              </button>
                              <button
                                onClick={previousTrack}
                                disabled={previousTracks.length === 0}
                                className="w-12 h-12 rounded-full bg-white/10 text-white flex items-center justify-center hover:bg-white/20 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                                title="Previous"
                              >
                                ⏮
                              </button>
                              <button
                                onClick={togglePlayPause}
                                className="w-16 h-16 rounded-full bg-white text-gray-900 flex items-center justify-center hover:scale-110 transition-transform shadow-lg"
                              >
                                {isPlaying ? '⏸' : '▶'}
                              </button>
                              <button
                                onClick={skipTrack}
                                className="w-12 h-12 rounded-full bg-white/10 text-white flex items-center justify-center hover:bg-white/20 transition-colors"
                                title="Next"
                              >
                                ⏭
                              </button>
                              <button
                                onClick={toggleRepeat}
                                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                                  repeatMode !== 'off' ? 'bg-green-500 text-white' : 'bg-white/10 text-gray-400 hover:text-white'
                                }`}
                                title={`Repeat: ${repeatMode}`}
                              >
                                {getRepeatIcon()}
                              </button>
                              <button
                                onClick={() => addToFavorites(currentTrack)}
                                className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                                  isInFavorites(currentTrack)
                                    ? 'bg-red-500 text-white'
                                    : 'bg-white/10 text-white hover:bg-white/20'
                                }`}
                                title="Add to favorites"
                              >
                                ❤️
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    </motion.div>
                  ) : (
                    <div className="flex items-center justify-center h-64">
                      <p className="text-gray-400 text-xl">
                        {isMonitoring ? 'Loading music...' : 'Click "Start Monitoring" to begin'}
                      </p>
                    </div>
                  )}
                </AnimatePresence>

                {/* Up Next */}
                {nextTracks.length > 0 && (
                  <div className="mt-8">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-gray-400 text-sm font-bold uppercase tracking-wider">
                        Up Next ({nextTracks.length})
                      </h3>
                      {nextTracks.length <= 2 && (
                        <button
                          onClick={() => requestMoreMusic(manualMood || currentMood)}
                          disabled={isLoadingMore}
                          className="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50"
                        >
                          {isLoadingMore ? 'Loading...' : '+ Load More'}
                        </button>
                      )}
                    </div>
                    <div className="space-y-2">
                      {nextTracks.slice(0, 5).map((track, index) => (
                        <motion.div
                          key={track.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 cursor-pointer transition-colors group"
                        >
                          <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0" onClick={() => selectTrack(track)}>
                            {track.artwork ? (
                              <img src={track.artwork} alt={track.name} className="w-full h-full object-cover" />
                            ) : (
                              <div className={`w-full h-full bg-gradient-to-br ${moodConfig.gradient} flex items-center justify-center text-xl`}>
                                {moodConfig.icon}
                              </div>
                            )}
                          </div>
                          <div className="flex-1 min-w-0" onClick={() => selectTrack(track)}>
                            <div className="text-white font-medium truncate text-sm">{track.name}</div>
                            <div className="text-gray-400 text-xs truncate">{track.artist}</div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              addToFavorites(track);
                            }}
                            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all text-sm ${
                              isInFavorites(track) ? 'text-red-500' : 'text-gray-500 hover:text-white'
                            }`}
                          >
                            ❤️
                          </button>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        ) : currentPage === 'favorites' ? (
          /* Favorites Page */
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glassmorphic glow rounded-3xl p-8"
            >
              <h2 className="text-3xl font-bold text-white mb-6 heading">❤️ Your Favorites</h2>
              
              {favorites.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-400 text-lg">No favorites yet!</p>
                  <p className="text-gray-500 mt-2">Click the ❤️ button on any track to add it here</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {favorites.map((track, index) => (
                    <motion.div
                      key={`${track.name}-${index}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group"
                    >
                      <div className="w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
                        {track.artwork ? (
                          <img src={track.artwork} alt={track.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-2xl">
                            🎵
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-white font-medium text-lg truncate">{track.name}</div>
                        <div className="text-gray-400 truncate">{track.artist}</div>
                        {track.mood && (
                          <div className="text-gray-500 text-sm mt-1">
                            {MOOD_CONFIG[track.mood]?.icon} {MOOD_CONFIG[track.mood]?.name}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          setCurrentTrack({ ...track, id: `fav-${index}` });
                          playTrack(track);
                          setCurrentPage('player');
                        }}
                        className="w-12 h-12 rounded-full bg-white/10 text-white flex items-center justify-center hover:bg-white/20 transition-colors"
                      >
                        ▶
                      </button>
                      <button
                        onClick={() => removeFromFavorites(track)}
                        className="w-12 h-12 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center hover:bg-red-500 hover:text-white transition-colors"
                      >
                        🗑️
                      </button>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        ) : (
          /* History Page */
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glassmorphic glow rounded-3xl p-8"
            >
              <h2 className="text-3xl font-bold text-white mb-6 heading">📜 Listening History</h2>
              
              {listeningHistory.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-400 text-lg">No listening history yet!</p>
                  <p className="text-gray-500 mt-2">Start listening to music to build your history</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {listeningHistory.map((track, index) => (
                    <motion.div
                      key={`${track.name}-${index}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                      className="flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                    >
                      <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0">
                        {track.artwork ? (
                          <img src={track.artwork} alt={track.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-xl">
                            🎵
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-white font-medium truncate">{track.name}</div>
                        <div className="text-gray-400 text-sm truncate">{track.artist}</div>
                        <div className="text-gray-500 text-xs mt-1">
                          {new Date(track.playedAt).toLocaleString()}
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setCurrentTrack({ ...track, id: `history-${index}` });
                          playTrack(track, false);
                          setCurrentPage('player');
                        }}
                        className="w-10 h-10 rounded-full bg-white/10 text-white flex items-center justify-center hover:bg-white/20 transition-colors"
                      >
                        ▶
                      </button>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BiometricMusicPlayer;