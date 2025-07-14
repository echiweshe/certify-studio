# Windows-Compatible Audio Processing Libraries

For Windows users, here are alternative audio processing options:

## Instead of pedalboard:
- **pydub** - Already included, handles basic audio effects
- **scipy.signal** - Already included, provides filters and signal processing
- **pyaudio** - For real-time audio I/O (optional)

## Additional Windows-compatible libraries:
```bash
# If you need more audio processing:
uv pip install pyaudio  # Real-time audio
uv pip install python-sounddevice  # Alternative audio I/O
uv pip install noisereduce  # Noise reduction
```

## Audio Processing Features Available:

### Built-in (no additional install):
- ✅ Audio file I/O (WAV, MP3, FLAC, etc.)
- ✅ Normalization
- ✅ Basic compression
- ✅ Silence detection
- ✅ Pitch detection
- ✅ Spectral analysis
- ✅ MFCC extraction
- ✅ Noise reduction
- ✅ Speech/music segmentation

### With optional libraries:
- 🎤 Real-time audio capture (pyaudio)
- 🎵 Advanced music analysis (madmom - if needed)
- 🔊 Real-time effects (python-sounddevice)

The platform includes all necessary audio processing for educational content without requiring pedalboard.
