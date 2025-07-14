@echo off
echo ============================================================
echo     Installing Vision & Audio Dependencies with UV
echo ============================================================
echo.

echo Installing computer vision dependencies...
uv add opencv-python opencv-contrib-python

echo.
echo Installing audio processing dependencies...
uv add librosa soundfile pydub webrtcvad

echo.
echo Installing additional dependencies...
uv add pytesseract pdf2image matplotlib seaborn moviepy imageio imageio-ffmpeg pyyaml

echo.
echo Syncing all dependencies...
uv sync --all-extras

echo.
echo ============================================================
echo     Dependencies installed! Starting Certify Studio...
echo ============================================================
echo.

uv run python scripts/uv_enterprise_start.py

pause
