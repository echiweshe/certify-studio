"""
Quick installation of known missing dependencies
"""

import subprocess

# Known missing dependencies based on the errors
deps_to_install = [
    "markdown",
    "pyyaml", 
    "beautifulsoup4",
    "lxml",
    "html2text",
]

print("=== Installing Missing Dependencies ===\n")

for dep in deps_to_install:
    print(f"Installing {dep}...")
    subprocess.run(f"uv add {dep}", shell=True)

print("\nSyncing...")
subprocess.run("uv sync", shell=True)

print("\nRunning tests...")
subprocess.run("uv run pytest tests/unit/test_simple.py -v", shell=True)
