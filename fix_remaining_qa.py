"""
Fix all import issues in QA modules comprehensively
"""

import os

qa_dir = r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio\src\certify_studio\agents\specialized\quality_assurance"

files = ["feedback_analyzer.py", "benchmark_manager.py", "continuous_monitor.py"]

for filename in files:
    filepath = os.path.join(qa_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add imports after settings import
        if "from ....core.llm import MultimodalLLM" not in content:
            content = content.replace(
                "from ....core.config import settings",
                "from ....core.config import settings\nfrom ....core.llm import MultimodalLLM\nfrom ....core.llm.multimodal_llm import MultimodalMessage"
            )
        
        # Fix duplicate Optional
        content = content.replace(", Optional, Optional", ", Optional")
        
        # Fix self.config = config to self.llm = llm or MultimodalLLM()
        content = content.replace("self.config = config", "self.llm = llm or MultimodalLLM()")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Fixed {filename}")

print("\nDone! Run test now.")
