#!/usr/bin/env python3
"""Fix all Pydantic v2 deprecation warnings"""

import re
from pathlib import Path

config_file = Path(r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio\src\certify_studio\config.py")
content = config_file.read_text()

# Remove all env= parameters from Field() - pydantic-settings handles this automatically
content = re.sub(r'Field\((.*?),\s*env="[^"]+"\)', r'Field(\1)', content)

# Fix Config class
content = content.replace('class Config:', 'model_config = ConfigDict(')
content = content.replace('env_file = ".env"', 'env_file=".env",')
content = content.replace('env_file_encoding = "utf-8"', 'env_file_encoding="utf-8",')
content = content.replace('case_sensitive = True', 'case_sensitive=True,')
content = content.replace('extra = "ignore"  # Ignore extra fields in .env file', 'extra="ignore"  # Ignore extra fields')

# Add ConfigDict import
if 'from pydantic import' in content and 'ConfigDict' not in content:
    content = content.replace(
        'from pydantic import Field, field_validator, SecretStr',
        'from pydantic import ConfigDict, Field, field_validator, SecretStr'
    )

# Fix the model_config indentation
content = re.sub(
    r'model_config = ConfigDict\(\n\s+env_file',
    'model_config = ConfigDict(\n        env_file',
    content
)

# Close the ConfigDict properly
content = re.sub(
    r'extra="ignore"  # Ignore extra fields\n\s+\n\s+# Settings source customization removed for compatibility',
    'extra="ignore"  # Ignore extra fields\n    )',
    content
)

config_file.write_text(content)
print("Fixed Pydantic v2 warnings in config.py")
