"""
Install all remaining missing dependencies
"""

import subprocess
import sys

def install_deps():
    """Install all missing dependencies we've discovered."""
    
    print("=== Installing All Missing Dependencies ===\n")
    
    # List of missing dependencies discovered
    missing_deps = [
        "markdown",  # For markdown parsing
        "beautifulsoup4",  # Often used with markdown
        "lxml",  # XML/HTML parsing
        "html2text",  # HTML to text conversion
        "markdownify",  # Convert HTML to markdown
    ]
    
    # Install each dependency
    for dep in missing_deps:
        print(f"Installing {dep}...")
        result = subprocess.run(
            f"uv add {dep}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ {dep} installed successfully")
        else:
            print(f"✗ Failed to install {dep}")
            if result.stderr:
                print(f"  Error: {result.stderr}")
    
    # Sync dependencies
    print("\nSyncing dependencies...")
    subprocess.run("uv sync", shell=True)
    
    # Run tests again
    print("\n=== Running Tests ===")
    result = subprocess.run(
        "uv run pytest tests/unit/test_simple.py -v",
        shell=True,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    if result.returncode != 0:
        print("\nTests still failing. Let's check what other imports might be missing...")
        
        # Try to run a more detailed import check
        print("\n=== Checking All Imports ===")
        subprocess.run("uv run python test_imports_uv.py", shell=True)

if __name__ == "__main__":
    install_deps()
