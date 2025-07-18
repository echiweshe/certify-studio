import sys
# Read the file and show lines around line 272
with open(r'C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\src\certify_studio\main.py', 'r') as f:
    lines = f.readlines()
    
# Show lines 265-275 (around line 272)
for i in range(max(0, 265), min(len(lines), 275)):
    print(f"{i+1}: {repr(lines[i])}")
