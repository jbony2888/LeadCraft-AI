#!/bin/bash

# LeadCraft AI Project Generator Script

echo "🚀 LeadCraft AI Project Generator"
echo "=================================="

# Check if LeadCraft-AI directory already exists
if [ -d "LeadCraft-AI" ]; then
    read -p "LeadCraft-AI directory already exists. Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Project generation cancelled."
        exit 1
    fi
    rm -rf LeadCraft-AI
fi

# Create project structure
echo "📁 Creating project structure..."
mkdir -p LeadCraft-AI/{static,templates}

# Create .env file
echo "🔧 Creating .env file..."
cat > LeadCraft-AI/.env << 'EOF'
# LeadCraft AI Environment Variables
# Replace with your actual OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Add other environment variables as needed
# FLASK_ENV=development
# FLASK_DEBUG=True
EOF

# Create requirements.txt
echo "📦 Creating requirements.txt..."
cat > LeadCraft-AI/requirements.txt << 'EOF'
flask==3.1.1
openai==1.97.0
chromadb==1.0.15
python-dotenv==1.0.0
reportlab==4.1.0
EOF

# Create README.md
echo "📖 Creating README.md..."
cat > LeadCraft-AI/README.md << 'EOF'
# LeadCraft AI

An AI-powered lead generation and qualification platform built with Flask, OpenAI, and ChromaDB.

## Quick Start

1. **Set up your environment:**
   ```bash
   cd LeadCraft-AI
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure your API key:**
   - Edit the `.env` file
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the application:**
   - Landing page: http://127.0.0.1:5000
   - Dashboard: http://127.0.0.1:5000/dashboard

## Features

- 🤖 AI-powered chatbot for lead qualification
- 📊 Admin dashboard for lead management
- 📧 Email capture and lead magnet delivery
- 📈 Lead scoring and analytics
- 📱 Responsive design
- 🔍 Semantic search with ChromaDB

Happy coding! 🎉
EOF

# Create setup script
echo "⚙️ Creating setup script..."
cat > LeadCraft-AI/setup.sh << 'EOF'
#!/bin/bash
# LeadCraft AI Setup Script

echo "🚀 Setting up LeadCraft AI..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file and add your OpenAI API key"
echo "2. Run: python app.py"
echo "3. Open http://127.0.0.1:5000 in your browser"
EOF

chmod +x LeadCraft-AI/setup.sh

echo "✅ Project structure created!"
echo ""
echo "Next steps:"
echo "1. cd LeadCraft-AI"
echo "2. Edit .env file and add your OpenAI API key"
echo "3. Run: python -m venv venv"
echo "4. Run: source venv/bin/activate (or venv\Scripts\activate on Windows)"
echo "5. Run: pip install -r requirements.txt"
echo "6. Copy your existing app.py, agent.py, and template files"
echo "7. Run: python app.py"
echo ""
echo "Or use the setup script:"
echo "1. cd LeadCraft-AI"
echo "2. Edit .env file and add your OpenAI API key"
echo "3. Run: ./setup.sh"
echo "4. Copy your existing files"
echo "5. Run: python app.py"
echo ""
echo "Happy coding! 🎉" 