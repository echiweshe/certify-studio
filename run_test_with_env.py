
import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import subprocess
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/unit/test_simple.py", "-v"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)
