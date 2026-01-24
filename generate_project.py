#!/usr/bin/env python3
"""
LeadCraft AI Project Generator
This script automatically creates the complete LeadCraft AI project structure and files.
Focus: Lead qualification, scoring, and CSV storage only.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_directory_structure():
    """Create the project directory structure"""
    directories = [
        'LeadCraft-AI',
        'LeadCraft-AI/static',
        'LeadCraft-AI/templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_env_file():
    """Create .env file template"""
    env_content = """# LeadCraft AI Environment Variables
# Replace with your actual OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Add other environment variables as needed
# FLASK_ENV=development
# FLASK_DEBUG=True
"""
    
    with open('LeadCraft-AI/.env', 'w') as f:
        f.write(env_content)
    print("✓ Created .env file template")

def create_requirements_file():
    """Create requirements.txt file"""
    requirements_content = """flask==3.1.1
openai==1.97.0
chromadb==1.0.15
python-dotenv==1.0.0
"""
    
    with open('LeadCraft-AI/requirements.txt', 'w') as f:
        f.write(requirements_content)
    print("✓ Created requirements.txt")

def create_faq_file():
    """Create FAQ content file"""
    faq_content = """What is LeadCraft AI?
LeadCraft AI is an AI-powered lead generation platform that helps businesses capture and qualify leads through intelligent chatbots.

How much does it cost?
We offer a free plan and premium plans starting at $29/month. Contact us for custom enterprise pricing.

What integrations do you support?
We integrate with popular CRMs like HubSpot, Salesforce, and Pipedrive, as well as email marketing platforms.

How quickly will I see results?
Most clients see their first qualified leads within 24-48 hours of setup.

Do you offer a free trial?
Yes! We offer a 14-day free trial with full access to all features.

What makes your AI different?
Our AI is specifically trained on sales conversations and lead qualification, making it more effective than generic chatbots.

How does the lead qualification work?
Our AI analyzes conversation context, buying intent, and engagement level to automatically qualify leads and assign scores.

Can I customize the chatbot responses?
Yes! You can customize responses, add your own FAQ content, and train the AI on your specific products and services.

What kind of leads do you generate?
We generate high-quality, pre-qualified leads that match your ideal customer profile and show genuine buying intent.

Do you provide analytics and reporting?
Yes! Our system provides detailed analytics on lead quality, conversion rates, and chatbot performance metrics.
"""
    
    with open('LeadCraft-AI/faq.txt', 'w') as f:
        f.write(faq_content)
    print("✓ Created faq.txt")

def create_lead_guide_file():
    """Create lead generation guide content"""
    guide_content = """10 LEAD GENERATION STRATEGIES THAT ACTUALLY WORK

This comprehensive guide will help you implement proven lead generation strategies that will attract qualified prospects and grow your business.

1. CONTENT MARKETING
Create valuable blog posts, videos, and infographics that solve your audience's problems. Use SEO to attract organic traffic.

2. SOCIAL MEDIA ENGAGEMENT
Build relationships on LinkedIn, Twitter, and Facebook. Share industry insights and engage with potential prospects.

3. EMAIL MARKETING
Build targeted email lists and create compelling lead magnets. Use automation for follow-up sequences.

4. REFERRAL PROGRAMS
Incentivize existing customers to refer others. Create a structured referral process.

5. PARTNERSHIPS
Collaborate with complementary businesses. Cross-promote each other's services.

6. WEBINARS AND EVENTS
Host educational webinars and attend industry conferences to network with prospects.

7. COLD OUTREACH
Research and personalize your approach. Use multiple channels and follow up consistently.

8. ACCOUNT-BASED MARKETING
Target specific high-value accounts with personalized campaigns.

9. INFLUENCER MARKETING
Partner with industry influencers to leverage their audience and credibility.

10. OPTIMIZATION AND TESTING
A/B test your landing pages and optimize your conversion funnel continuously.
"""
    
    with open('LeadCraft-AI/lead_generation_guide.txt', 'w') as f:
        f.write(guide_content)
    print("✓ Created lead_generation_guide.txt")

def create_app_py():
    """Create the main Flask application file"""
    app_content = '''from flask import Flask, render_template, request, jsonify
from agent import run_agent
import json
from datetime import datetime
import os
import csv

app = Flask(__name__)

# Store captured emails (in production, use a database)
captured_emails = []

def save_lead_to_csv(lead_data):
    """Save lead data to CSV file for Excel compatibility"""
    csv_file = 'leads.csv'
    file_exists = os.path.isfile(csv_file)
    
    # Define CSV headers
    fieldnames = ['timestamp', 'name', 'email', 'product', 'pain_point', 'session_id', 'lead_score']
    
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write headers if file doesn't exist
            if not file_exists:
                writer.writeheader()
            
            # Write lead data
            writer.writerow({
                'timestamp': lead_data.get('timestamp', datetime.now().isoformat()),
                'name': lead_data.get('name', ''),
                'email': lead_data.get('email', ''),
                'product': lead_data.get('product', ''),
                'pain_point': lead_data.get('pain_point', ''),
                'session_id': lead_data.get('session_id', ''),
                'lead_score': lead_data.get('lead_score', 0)
            })
        
        print(f"Lead saved to CSV: {lead_data.get('name', 'Unknown')} ({lead_data.get('email', 'No email')}) - Score: {lead_data.get('lead_score', 0)}")
        return True
    except Exception as e:
        print(f"Error saving lead to CSV: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Get response from agent
        response = run_agent(user_message, session_id)
        
        # Check if we should offer the lead magnet
        should_offer_lead_magnet = check_lead_magnet_trigger(user_message, response)
        
        # Generate suggested questions based on the conversation
        suggested_questions = generate_suggested_questions(user_message, response)
        
        return jsonify({
            'response': response,
            'show_email_capture': should_offer_lead_magnet,
            'suggested_questions': suggested_questions
        })
        
    except Exception as e:
        return jsonify({
            'response': 'Sorry, I encountered an error. Please try again.',
            'show_email_capture': False,
            'suggested_questions': []
        }), 500

@app.route('/capture-email', methods=['POST'])
def capture_email():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'message': 'Invalid email address'})
        
        # Store the email (in production, save to database)
        email_record = {
            'email': email,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'source': 'chatbot_lead_magnet'
        }
        captured_emails.append(email_record)
        
        print(f"Email captured: {email} from session {session_id}")
        
        return jsonify({'success': True, 'message': 'Email captured successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error capturing email'}), 500

@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    """Handle lead submission from chatbot qualification flow"""
    try:
        data = request.get_json()
        
        # Extract lead data
        lead_data = {
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'product': data.get('product', ''),
            'pain_point': data.get('pain_point', ''),
            'session_id': data.get('session_id', 'default'),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'source': 'chatbot_lead_qualification',
            'lead_score': data.get('lead_score', 0)
        }
        
        # Validate required fields
        if not lead_data['name'] or not lead_data['email']:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Store the lead (in production, save to database)
        captured_emails.append(lead_data)
        
        # Save lead to CSV file for Excel compatibility
        csv_saved = save_lead_to_csv(lead_data)
        
        print(f"Lead captured: {lead_data['name']} ({lead_data['email']}) from session {lead_data['session_id']}")
        print(f"Product: {lead_data['product']}")
        print(f"Pain point: {lead_data['pain_point']}")
        print(f"Lead score: {lead_data['lead_score']}")
        print(f"CSV saved: {csv_saved}")
        
        return jsonify({
            'success': True, 
            'message': 'Lead captured successfully',
            'lead_id': f"lead_{len(captured_emails)}",
            'lead_score': lead_data['lead_score']
        })
        
    except Exception as e:
        print(f"Error capturing lead: {e}")
        return jsonify({'success': False, 'message': 'Error capturing lead'}), 500

def check_lead_magnet_trigger(user_message, agent_response):
    """Determine if we should offer the lead magnet based on user message and response"""
    user_lower = user_message.lower()
    
    # Trigger words that indicate interest in lead generation
    trigger_words = [
        'lead', 'leads', 'generation', 'prospecting', 'sales', 'outreach',
        'automation', 'strategy', 'guide', 'pdf', 'download', 'free',
        'how to', 'tips', 'best practices', 'strategies'
    ]
    
    # Check if user message contains trigger words
    has_trigger_words = any(word in user_lower for word in trigger_words)
    
    # Check if this is a qualified lead (shows buying intent)
    is_qualified = any(word in user_lower for word in ['pricing', 'cost', 'plan', 'demo', 'trial', 'start'])
    
    return has_trigger_words or is_qualified

def generate_suggested_questions(user_message, agent_response):
    """Generate contextual suggested questions based on the conversation"""
    user_lower = user_message.lower()
    
    # Default suggestions
    default_suggestions = [
        "What does LeadCraft AI do?",
        "Is there a free plan?",
        "Show me pricing"
    ]
    
    # Contextual suggestions based on conversation
    if any(word in user_lower for word in ['pricing', 'cost', 'plan', 'price']):
        return [
            "What's included in the premium plan?",
            "Is there a free trial?",
            "Can I cancel anytime?"
        ]
    
    elif any(word in user_lower for word in ['integration', 'connect', 'crm', 'hubspot']):
        return [
            "What other integrations do you support?",
            "How does the setup process work?",
            "Can I import my existing contacts?"
        ]
    
    elif any(word in user_lower for word in ['demo', 'trial', 'test', 'start']):
        return [
            "How do I get started?",
            "What's the setup time?",
            "Do you offer onboarding support?"
        ]
    
    elif any(word in user_lower for word in ['lead', 'leads', 'generation']):
        return [
            "How quickly will I see results?",
            "What kind of leads do you generate?",
            "Can I customize the AI responses?"
        ]
    
    # Return default suggestions if no specific context
    return default_suggestions[:3]

@app.route('/captured-emails')
def get_captured_emails():
    """Admin endpoint to view captured emails (for testing)"""
    return jsonify(captured_emails)

if __name__ == '__main__':
    app.run(debug=True)
'''
    
    with open('LeadCraft-AI/app.py', 'w') as f:
        f.write(app_content)
    print("✓ Created app.py")

def create_agent_py():
    """Create the AI agent file"""
    agent_content = '''import os
import openai
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up Chroma and embed the FAQ file
chroma_client = chromadb.Client()
chroma_collection = chroma_client.create_collection(name="faq")

# Conversation memory
conversation_history = {}

def load_faq():
    with open("faq.txt", "r") as f:
        docs = f.read().split("\\n\\n")
    for i, doc in enumerate(docs):
        chroma_collection.add(
            documents=[doc],
            metadatas=[{"source": f"faq_{i}"}],
            ids=[f"id_{i}"]
        )

# Load once on startup
load_faq()

def search_docs(query):
    results = chroma_collection.query(query_texts=[query], n_results=1)
    if results["documents"]:
        # Extract just the answer part (after the question)
        full_doc = results["documents"][0][0]
        if "?" in full_doc:
            # Split on the first question mark and return the answer part
            parts = full_doc.split("?", 1)
            if len(parts) > 1:
                return parts[1].strip()
        return full_doc
    return "Sorry, I couldn't find an answer for that."

def respond_to_objection(text):
    lower = text.lower()
    if "too expensive" in lower:
        return "I understand the concern! We also offer a free plan and competitive pricing for startups."
    elif "not sure" in lower or "don't know" in lower:
        return "No worries — I can help explain more or share a quick demo link."
    return None

def qualify_lead(user_input, session_id):
    """Analyze if this is a qualified lead and return a score"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a lead qualification expert. Analyze the user's message and return a score from 0-10 based on buying intent, where 0=no interest, 5=moderate interest, 10=highly qualified. Return only the number."},
                {"role": "user", "content": f"User message: {user_input}"}
            ],
            max_tokens=5,
            temperature=0.1
        )
        score = response.choices[0].message.content.strip()
        try:
            return int(score)
        except:
            return 0
    except:
        return 0

def generate_follow_up(user_input, session_id):
    """Generate contextual follow-up questions"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sales assistant. Generate 1-2 relevant follow-up questions to continue the conversation naturally. Keep them short and specific."},
                {"role": "user", "content": f"User said: {user_input}\\n\\nGenerate follow-up questions:"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except:
        return ""

def run_agent(user_input, session_id="default"):
    # Initialize session if new
    if session_id not in conversation_history:
        conversation_history[session_id] = {
            "messages": [],
            "lead_score": 0,
            "last_contact": datetime.now().isoformat(),
            "guide_offered": False
        }
    
    # Add user message to history
    conversation_history[session_id]["messages"].append({"role": "user", "content": user_input})
    
    # Check for objections first
    objection_response = respond_to_objection(user_input)
    if objection_response:
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": objection_response})
        return objection_response

    # Get relevant FAQ context
    faq_context = search_docs(user_input)
    
    # Qualify the lead and get score
    lead_score = qualify_lead(user_input, session_id)
    conversation_history[session_id]["lead_score"] = max(conversation_history[session_id]["lead_score"], lead_score)
    
    # Generate response with context
    try:
        # Build conversation context
        recent_messages = conversation_history[session_id]["messages"][-3:]  # Last 3 messages
        context = "\\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"""You are a dynamic sales assistant. 
                - Be conversational and engaging
                - Use the FAQ information provided
                - If lead_score is high, be more direct about next steps
                - Keep responses under 100 words
                - Be enthusiastic but professional"""},
                {"role": "user", "content": f"""Context: {context}
                FAQ Info: {faq_context}
                Lead Score: {conversation_history[session_id]['lead_score']}
                User: {user_input}"""}
            ],
            max_tokens=150,
            temperature=0.8
        )
        
        main_response = response.choices[0].message.content.strip()
        
        # Offer guide if qualified and not already offered
        if conversation_history[session_id]["lead_score"] >= 6 and not conversation_history[session_id]["guide_offered"]:
            main_response += "\\n\\n📚 **Free Guide**: I'd love to send you our comprehensive guide on lead generation strategies. It's packed with actionable tips that have helped our clients double their leads in 30 days. Would you like me to send it to your email?"
            conversation_history[session_id]["guide_offered"] = True
        
        # Generate follow-up if lead is qualified
        follow_up = ""
        if conversation_history[session_id]["lead_score"] >= 4 and not conversation_history[session_id]["guide_offered"]:
            follow_up = generate_follow_up(user_input, session_id)
            if follow_up:
                main_response += f"\\n\\n{follow_up}"
        
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": main_response})
        return main_response
        
    except Exception as e:
        # Fallback to direct FAQ response
        fallback_response = faq_context if faq_context != "Sorry, I couldn't find an answer for that." else "I'd be happy to help! Could you tell me more about what you're looking for?"
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": fallback_response})
        return fallback_response

def get_lead_score(session_id):
    """Get the current lead score for a session"""
    if session_id in conversation_history:
        return conversation_history[session_id]["lead_score"]
    return 0
'''
    
    with open('LeadCraft-AI/agent.py', 'w') as f:
        f.write(agent_content)
    print("✓ Created agent.py")

def create_readme():
    """Create README.md file"""
    readme_content = '''# LeadCraft AI

An AI-powered lead generation and qualification platform built with Flask, OpenAI, and ChromaDB.

## Features

- 🤖 AI-powered chatbot for lead qualification
- 📊 Lead scoring and qualification
- 📧 Email capture and lead magnet delivery
- 📈 CSV storage for lead data
- 📱 Responsive design
- 🔍 Semantic search with ChromaDB

## Quick Start

1. **Set up your environment:**
   ```bash
   cd LeadCraft-AI
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
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

## Project Structure

```
LeadCraft-AI/
├── app.py                 # Main Flask application
├── agent.py              # AI agent logic
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── faq.txt              # FAQ content for semantic search
├── lead_generation_guide.txt  # Lead magnet content
├── leads.csv            # Lead storage (auto-generated)
├── static/
│   └── style.css        # Landing page styles
└── templates/
    └── index.html       # Landing page
```

## How It Works

1. **Lead Capture**: Users interact with the AI chatbot on the landing page
2. **Qualification**: The AI analyzes conversations and qualifies leads based on intent
3. **Scoring**: Each lead is assigned a score from 0-10 based on buying intent
4. **Lead Magnet**: Qualified leads are offered a free guide in exchange for their email
5. **Storage**: All leads are stored in a CSV file with scores and details

## Lead Scoring

The system automatically scores leads based on:
- **Buying intent indicators** (pricing, cost, plan, demo)
- **Engagement level** (conversation length, questions asked)
- **Conversation quality** (specific vs general questions)
- **Keywords** (interested, looking for, need help)

Lead scores range from 0-10, where:
- 0-3: Low interest
- 4-6: Moderate interest
- 7-10: High interest/qualified

## Customization

- **FAQ Content**: Edit `faq.txt` to customize chatbot responses
- **Lead Magnet**: Modify `lead_generation_guide.txt` for your content
- **Styling**: Update CSS files in the `static/` directory
- **AI Behavior**: Adjust the agent logic in `agent.py`

## Production Deployment

For production use, consider:
- Using a production WSGI server (Gunicorn)
- Setting up a proper database (PostgreSQL)
- Implementing email service integration
- Adding SSL certificates
- Setting up monitoring and logging

## License

This project is open source and available under the MIT License.

## Support

For questions or support, please refer to the tutorial documentation or create an issue in the repository.
'''
    
    with open('LeadCraft-AI/README.md', 'w') as f:
        f.write(readme_content)
    print("✓ Created README.md")

def create_setup_script():
    """Create a setup script for easy installation"""
    setup_content = '''#!/bin/bash
# LeadCraft AI Setup Script

echo "🚀 Setting up LeadCraft AI..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ Python and pip are installed"

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
echo ""
echo "Happy coding! 🎉"
'''
    
    with open('LeadCraft-AI/setup.sh', 'w') as f:
        f.write(setup_content)
    
    # Make the script executable
    os.chmod('LeadCraft-AI/setup.sh', 0o755)
    print("✓ Created setup.sh")

def main():
    """Main function to generate the project"""
    print("🚀 LeadCraft AI Project Generator")
    print("Focus: Lead Qualification, Scoring, and CSV Storage")
    print("=" * 50)
    
    # Check if LeadCraft-AI directory already exists
    if os.path.exists('LeadCraft-AI'):
        response = input("LeadCraft-AI directory already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Project generation cancelled.")
            return
        shutil.rmtree('LeadCraft-AI')
    
    # Create project structure
    create_directory_structure()
    create_env_file()
    create_requirements_file()
    create_faq_file()
    create_lead_guide_file()
    create_app_py()
    create_agent_py()
    create_readme()
    create_setup_script()
    
    print("\n" + "=" * 50)
    print("✅ Project generated successfully!")
    print("\nNext steps:")
    print("1. cd LeadCraft-AI")
    print("2. Edit .env file and add your OpenAI API key")
    print("3. Run: python -m venv venv")
    print("4. Run: source venv/bin/activate (or venv\\Scripts\\activate on Windows)")
    print("5. Run: pip install -r requirements.txt")
    print("6. Run: python app.py")
    print("7. Open http://127.0.0.1:5000 in your browser")
    print("\nOr use the setup script:")
    print("1. cd LeadCraft-AI")
    print("2. Edit .env file and add your OpenAI API key")
    print("3. Run: ./setup.sh")
    print("4. Run: python app.py")
    print("\nHappy coding! 🎉")

if __name__ == "__main__":
    main() 