#!/usr/bin/env bash
# Quick deploy script - Commit and push Docker deployment configs

set -e

echo "🐳 Audio Fetch - Docker Deployment to Render"
echo "============================================="
echo ""

# Check if git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not a git repository. Run 'git init' first."
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "📦 Staging Docker deployment files..."
    git add render.yaml Dockerfile requirements-prod.txt .dockerignore
    git add DOCKER_DEPLOY_GUIDE.md DEPLOYMENT_CHECKLIST.md
    git add docs/RENDER_DEPLOYMENT.md .env.example
    git add build.sh start.sh
    git add main.py  # Updated CORS config
    
    echo "✅ Files staged"
    echo ""
    echo "📝 Creating commit..."
    git commit -m "Add Docker deployment configuration with FFmpeg support

- Add Dockerfile with Python 3.11, FFmpeg, and curl
- Configure render.yaml for Docker runtime
- Add production requirements (requirements-prod.txt)
- Optimize with .dockerignore
- Update main.py with environment-based CORS
- Add comprehensive deployment documentation
- Include build and start scripts

Ready to deploy on Render free plan with full format support (mp3, opus, wav, m4a)"
    
    echo "✅ Commit created"
else
    echo "✅ No uncommitted changes (already committed)"
fi

echo ""
echo "🚀 Ready to push to GitHub!"
echo ""
echo "Run:"
echo "  git push origin main"
echo ""
echo "Then follow DOCKER_DEPLOY_GUIDE.md to deploy on Render"
