#!/bin/bash
# Git setup and push script for Certify Studio

echo "🚀 Certify Studio - Git Setup and Push Script"
echo "============================================="

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git repository initialized"
fi

# Configure git (optional - update with your details)
echo "
📝 Git Configuration
If you haven't configured git, uncomment and update these lines:"
echo "# git config user.name 'Your Name'"
echo "# git config user.email 'your.email@example.com'"

# Add all files
echo "
📂 Adding all files to git..."
git add -A
echo "✅ All files added"

# Show status
echo "
📊 Git Status:"
git status --short

# Create initial commit
echo "
💾 Creating initial commit..."
git commit -F COMMIT_MESSAGE.txt
echo "✅ Initial commit created"

# Add remote (update with your repository URL)
echo "
🔗 Add your remote repository:"
echo "git remote add origin https://github.com/YOUR_USERNAME/certify-studio.git"
echo "
Or if using SSH:"
echo "git remote add origin git@github.com:YOUR_USERNAME/certify-studio.git"

# Push instructions
echo "
📤 To push to GitHub:"
echo "1. Create a new repository on GitHub named 'certify-studio'"
echo "2. Don't initialize it with README, license, or .gitignore"
echo "3. Run: git remote add origin <your-repo-url>"
echo "4. Run: git branch -M main"
echo "5. Run: git push -u origin main"

echo "
✨ Done! Your code is ready to be pushed to GitHub."
