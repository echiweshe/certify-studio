# Python 3.12 Setup Guide for Certify Studio

## Why Python 3.12?

Python 3.13 (released October 2024) is too new for many scientific and audio processing libraries:
- ❌ **librosa** - Not compatible
- ❌ **torchaudio** - Not compatible  
- ❌ **webrtcvad** - Build failures
- ❌ **pedalboard** - No Windows wheels

Python 3.12 gives us:
- ✅ Full compatibility with all audio/ML libraries
- ✅ Better performance for scientific computing
- ✅ Stable ecosystem with mature packages
- ✅ All features of our original vision

## Quick Setup (Recommended)

### Option 1: Using UV (Easiest)
```bash
# Windows
setup_python312.bat

# Or manually:
uv python install 3.12
uv venv --python 3.12
uv sync --all-extras
```

### Option 2: Direct Python 3.12 Install
1. Download Python 3.12.7 from https://www.python.org/downloads/release/python-3127/
2. Install with "Add to PATH" checked
3. Run:
```bash
python3.12 -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

pip install uv
uv sync --all-extras
```

## After Setup

1. **Copy the full-featured config:**
```bash
copy pyproject_python312.toml pyproject.toml
```

2. **Sync dependencies:**
```bash
uv sync --all-extras
```

3. **Launch the platform:**
```bash
uv run python scripts/launch.py
```

## What You Get with Python 3.12

### Full Audio Processing Suite
- Advanced speech recognition
- Professional audio effects
- Real-time processing
- Educational audio optimization

### Complete ML Pipeline
- All transformer models
- Audio embeddings
- Speech synthesis
- Music generation

### Enterprise Features
- Production-ready performance
- Full Windows/Linux/Mac support
- All original vision features

## Verification

Run this to verify your setup:
```bash
uv run python -c "import sys; print(f'Python {sys.version}')"
uv run python -c "import librosa, torch, torchaudio; print('✅ All audio libraries working!')"
```

## Troubleshooting

### If UV doesn't work:
```bash
# Install UV first
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### If packages fail to install:
```bash
# Clear cache and retry
uv cache clean
uv sync --all-extras --reinstall
```

### For Windows users:
- You might need Visual C++ Build Tools for some packages
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

## Benefits of Python 3.12

1. **100% Feature Compatibility** - Everything works as designed
2. **Better Performance** - Optimized libraries
3. **Stable Ecosystem** - Mature, tested packages
4. **Future-Proof** - Supported until 2028

## Next Steps

Once on Python 3.12, you can:
- Use the original `audio_processor.py` with full librosa support
- Enable all ML models and transformers
- Access professional audio effects
- Generate high-quality educational content

The platform will run at its full potential! 🚀
