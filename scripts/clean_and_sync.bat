@echo off
echo Cleaning UV cache and lock file...

REM Remove uv.lock if it exists
if exist uv.lock (
    echo Removing uv.lock...
    del uv.lock
)

REM Clear UV cache
echo Clearing UV cache...
uv cache clean

REM Sync dependencies fresh
echo Re-syncing dependencies...
uv sync --all-extras

echo Done! Now try running the application.
