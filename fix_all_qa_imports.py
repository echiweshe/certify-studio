"""
Fix all import issues in quality assurance modules
"""

import os
import re

def fix_qa_imports():
    qa_dir = r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio\src\certify_studio\agents\specialized\quality_assurance"
    
    # List of files to fix
    files_to_fix = [
        "performance_monitor.py",
        "feedback_analyzer.py", 
        "benchmark_manager.py",
        "continuous_monitor.py"
    ]
    
    replacements = [
        # Fix Config import
        (r'from \.\.\.\.core\.config import Config', 'from ....core.config import settings'),
        
        # Fix LLMClient import
        (r'from \.\.\.\.core\.llm import LLMClient', 'from ....core.llm import MultimodalLLM\nfrom ....core.llm.multimodal_llm import MultimodalMessage'),
        
        # Fix constructor - Config parameter
        (r'def __init__\(self, config: Config\):', 'def __init__(self, llm: Optional[MultimodalLLM] = None):'),
        
        # Fix constructor body
        (r'self\.config = config\s*\n\s*self\.llm_client = LLMClient\(config\)', 'self.llm = llm or MultimodalLLM()'),
        
        # Fix llm_client references
        (r'self\.llm_client\.generate\(', 'self.llm.generate([MultimodalMessage(text='),
        
        # Add closing for MultimodalMessage
        (r'self\.llm\.generate\(\[MultimodalMessage\(text=prompt\)', 'self.llm.generate([MultimodalMessage(text=prompt)])'),
        
        # Add Optional import if needed
        (r'from typing import (.*)', r'from typing import \1, Optional')
    ]
    
    for filename in files_to_fix:
        filepath = os.path.join(qa_dir, filename)
        if os.path.exists(filepath):
            print(f"Fixing {filename}...")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply replacements
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Fix any response = await self.llm.generate() calls
            content = re.sub(
                r'response = await self\.llm\.generate\(\[MultimodalMessage\(text=(\w+)\)\]\)',
                r'response = await self.llm.generate([MultimodalMessage(text=\1)])\n            response_text = response.text',
                content
            )
            
            # Fix json.loads(response) to json.loads(response_text)
            content = re.sub(
                r'json\.loads\(response\)',
                'json.loads(response_text)',
                content
            )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Fixed {filename}")

if __name__ == "__main__":
    fix_qa_imports()
    print("\nAll QA module imports fixed!")
    print("\nNow run: test_cert_aligner.bat")
