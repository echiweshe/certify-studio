"""
Script to integrate frontend connector with main app
"""

import sys
from pathlib import Path

def add_frontend_connector():
    """Add frontend connector import and setup to main.py"""
    
    main_file = Path("src/certify_studio/main.py")
    
    # Read current content
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if already added
    if "frontend_connector" in content:
        print("Frontend connector already integrated!")
        return
    
    # Find where to add the import
    import_section_end = content.find("# Configure logging")
    
    # Add import statement
    new_import = "from .frontend_connector import setup_frontend_connector\n"
    content = content[:import_section_end] + new_import + content[import_section_end:]
    
    # Find where to add the setup call in create_application
    app_creation_point = content.find("# Include API routes")
    setup_call = """    # Setup frontend connector for real-time updates
    try:
        from .frontend_connector import setup_frontend_connector
        asyncio.create_task(setup_frontend_connector(app))
        logger.info("Frontend connector initialized")
    except ImportError as e:
        logger.warning(f"Frontend connector not available: {e}")
    
    """
    
    # Insert the setup call
    content = content[:app_creation_point] + setup_call + content[app_creation_point:]
    
    # Write back
    with open(main_file, 'w') as f:
        f.write(content)
    
    print("✓ Frontend connector integrated successfully!")
    print("  - Import added")
    print("  - Setup call added to create_application()")
    print("\nRestart the backend to apply changes.")

if __name__ == "__main__":
    add_frontend_connector()
