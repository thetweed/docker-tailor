#!/bin/bash

echo "🎯 Job Tracker Setup Script"
echo ""

# Check Python version
echo "🐍 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.8+"; exit 1; }

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright
echo "🎭 Installing Playwright browsers (this may take a minute)..."
playwright install chromium

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads flask_session data

# Create .env from example
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    if [ -f .env.example ]; then
        cp .env.example .env
        # Auto-generate a secret key (works on macOS and Linux)
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        sed -i.bak "s/your-secret-key-here/$SECRET_KEY/" .env && rm -f .env.bak
        echo "   FLASK_SECRET_KEY has been auto-generated."
        echo "⚠️  IMPORTANT: Edit .env and add your Anthropic API key!"
    else
        echo "Creating .env with template..."
        cat > .env << 'EOF'
# Anthropic API Key
ANTHROPIC_API_KEY=your-api-key-here

# Flask Secret Key (generate a random string)
FLASK_SECRET_KEY=your-secret-key-here
EOF
        echo "⚠️  IMPORTANT: Edit .env and add your Anthropic API key!"
    fi
else
    echo "✓ .env file already exists"
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "
from app import create_app
app = create_app()
with app.app_context():
    print('✓ Database initialized')
" 2>/dev/null || echo "ℹ️  Database will be initialized on first run"

echo ""
echo "✨ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env and add your Anthropic API key"
echo "      Get one at: https://console.anthropic.com/settings/keys"
echo ""
echo "   2. Start the app:"
echo "      python app.py"
echo ""
echo "   3. Open your browser:"
echo "      http://localhost:5000"
echo ""
echo "💡 Tip: Keep this terminal window open while the app is running"
echo ""