"""
Auto-Fix Launcher for Certify Studio
Continuously launches, detects errors, and fixes them automatically
"""

import subprocess
import sys
import re
import time
from pathlib import Path
import asyncio

class AutoFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_path = self.project_root / "src"
        self.launch_script = self.project_root / "scripts" / "launch_clean.py"
        self.max_attempts = 50
        self.fixed_issues = []
        
    def run_server(self):
        """Run the server and capture output"""
        print("\n🚀 Attempting to start server...")
        process = subprocess.Popen(
            [sys.executable, str(self.launch_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=self.project_root
        )
        
        output = []
        error_found = False
        error_details = None
        
        # Wait for error or successful start
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 second timeout
            line = process.stdout.readline()
            if not line:
                break
                
            print(line.rstrip())
            output.append(line)
            
            # Check for errors
            if "ModuleNotFoundError:" in line:
                error_found = True
                error_details = self.parse_module_error(line, output)
            elif "ImportError:" in line:
                error_found = True
                error_details = self.parse_import_error(line, output)
            elif "SyntaxError:" in line:
                error_found = True
                error_details = self.parse_syntax_error(line, output)
            elif "Starting Certify Studio server..." in line:
                print("\n✅ Server started successfully!")
                return True, None
                
            if error_found:
                process.terminate()
                break
                
        process.terminate()
        return not error_found, error_details
    
    def parse_module_error(self, error_line, output):
        """Parse ModuleNotFoundError"""
        match = re.search(r"No module named '(.+)'", error_line)
        if match:
            module = match.group(1)
            # Get the file causing the import
            for line in reversed(output[-20:]):
                file_match = re.search(r'File "(.+\.py)", line (\d+)', line)
                if file_match:
                    return {
                        'type': 'module_not_found',
                        'module': module,
                        'file': file_match.group(1),
                        'line': int(file_match.group(2))
                    }
        return None
    
    def parse_import_error(self, error_line, output):
        """Parse ImportError"""
        match = re.search(r"cannot import name '(.+)' from '(.+)'", error_line)
        if match:
            name = match.group(1)
            module = match.group(2)
            # Get the file causing the import
            for line in reversed(output[-20:]):
                file_match = re.search(r'File "(.+\.py)", line (\d+)', line)
                if file_match:
                    return {
                        'type': 'import_error',
                        'name': name,
                        'module': module,
                        'file': file_match.group(1),
                        'line': int(file_match.group(2))
                    }
        return None
    
    def parse_syntax_error(self, error_line, output):
        """Parse SyntaxError"""
        # Find the file and line
        for i, line in enumerate(output[-20:]):
            if "File" in line and ".py" in line:
                file_match = re.search(r'File "(.+\.py)", line (\d+)', line)
                if file_match:
                    return {
                        'type': 'syntax_error',
                        'file': file_match.group(1),
                        'line': int(file_match.group(2)),
                        'details': error_line
                    }
        return None
    
    async def fix_error(self, error_details):
        """Fix the detected error"""
        if not error_details:
            return False
            
        print(f"\n🔧 Fixing {error_details['type']}...")
        
        if error_details['type'] == 'module_not_found':
            return await self.fix_module_not_found(error_details)
        elif error_details['type'] == 'import_error':
            return await self.fix_import_error(error_details)
        elif error_details['type'] == 'syntax_error':
            return await self.fix_syntax_error(error_details)
            
        return False
    
    async def fix_module_not_found(self, error):
        """Fix ModuleNotFoundError"""
        module = error['module']
        file_path = Path(error['file'])
        
        print(f"Module '{module}' not found in {file_path.name}")
        
        # Common fixes
        if module == 'certify_studio.multimodal':
            # The module path is wrong, fix the import
            return await self.fix_import_path(file_path, error['line'], 
                                            "from ..multimodal.llm_router import LLMRouter",
                                            "from ..core.llm import MultimodalLLM as LLMRouter")
        
        elif module.startswith('certify_studio.'):
            # Check if it's a path issue
            parts = module.split('.')
            if len(parts) > 2:
                # Try to find the correct path
                possible_paths = [
                    'core', 'agents', 'api', 'domain', 'knowledge', 'media'
                ]
                for path in possible_paths:
                    if path in parts:
                        # Module might be in wrong location
                        print(f"Checking if module should be in {path}...")
                        
        return False
    
    async def fix_import_error(self, error):
        """Fix ImportError"""
        name = error['name']
        module = error['module']
        file_path = Path(error['file'])
        
        print(f"Cannot import '{name}' from '{module}' in {file_path.name}")
        
        # Common name mismatches
        name_fixes = {
            'MultiModalLLM': 'MultimodalLLM',
            'ConceptRelationship': 'Relationship',
            'Procedure': None,  # Remove this import
            'PlanStep': None,  # Define locally
        }
        
        if name in name_fixes:
            if name_fixes[name] is None:
                # Remove the import
                return await self.remove_import(file_path, name)
            else:
                # Replace the name
                return await self.replace_import_name(file_path, name, name_fixes[name])
                
        return False
    
    async def fix_syntax_error(self, error):
        """Fix SyntaxError"""
        file_path = Path(error['file'])
        line_num = error['line']
        
        print(f"Syntax error at line {line_num} in {file_path.name}")
        
        # Read the problematic line
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if line_num <= len(lines):
                problem_line = lines[line_num - 1]
                print(f"Problem line: {problem_line.strip()}")
                
                # Common syntax fixes
                if "**" in problem_line and "if" in problem_line:
                    # Fix unpacking syntax
                    fixed_line = problem_line.replace("**context if context else {}", "**(context if context else {})")
                    lines[line_num - 1] = fixed_line
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    print("✅ Fixed syntax error")
                    return True
                    
        return False
    
    async def fix_import_path(self, file_path, line_num, old_import, new_import):
        """Fix an import path"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if old_import in content:
            content = content.replace(old_import, new_import)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed import: {old_import} -> {new_import}")
            return True
            
        return False
    
    async def replace_import_name(self, file_path, old_name, new_name):
        """Replace an import name"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace in imports
        patterns = [
            f"from .+ import .+{old_name}",
            f"import .+{old_name}",
            f"{old_name},"
        ]
        
        modified = False
        for pattern in patterns:
            if re.search(pattern, content):
                content = re.sub(f"\\b{old_name}\\b", new_name, content)
                modified = True
                
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Replaced {old_name} with {new_name}")
            return True
            
        return False
    
    async def remove_import(self, file_path, import_name):
        """Remove an import"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        new_lines = []
        removed = False
        
        for line in lines:
            if import_name in line and ("import" in line or "from" in line):
                # Skip this line or remove just the name
                if f", {import_name}" in line:
                    line = line.replace(f", {import_name}", "")
                    new_lines.append(line)
                elif f"{import_name}," in line:
                    line = line.replace(f"{import_name},", "")
                    new_lines.append(line)
                elif f"import {import_name}" in line:
                    removed = True
                    continue
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        if removed or new_lines != lines:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"✅ Removed import: {import_name}")
            return True
            
        return False
    
    async def run(self):
        """Main auto-fix loop"""
        print("🤖 Auto-Fix Launcher Started")
        print("=" * 60)
        
        attempt = 0
        while attempt < self.max_attempts:
            attempt += 1
            print(f"\n📍 Attempt {attempt}/{self.max_attempts}")
            
            # Try to run the server
            success, error_details = self.run_server()
            
            if success:
                print("\n🎉 Server is running successfully!")
                print(f"Fixed {len(self.fixed_issues)} issues:")
                for issue in self.fixed_issues:
                    print(f"  - {issue}")
                break
                
            # Fix the error
            if error_details:
                fixed = await self.fix_error(error_details)
                if fixed:
                    self.fixed_issues.append(f"{error_details['type']}: {error_details.get('name', error_details.get('module', 'syntax'))}")
                    time.sleep(1)  # Brief pause before retry
                else:
                    print(f"\n❌ Could not automatically fix: {error_details}")
                    break
            else:
                print("\n❌ Unknown error occurred")
                break
                
        if attempt >= self.max_attempts:
            print(f"\n❌ Reached maximum attempts ({self.max_attempts})")

if __name__ == "__main__":
    fixer = AutoFixer()
    asyncio.run(fixer.run())
