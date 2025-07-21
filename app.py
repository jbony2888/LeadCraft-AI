from flask import Flask, render_template, request, jsonify, send_file
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
    fieldnames = ['timestamp', 'name', 'email', 'product', 'pain_point', 'session_id']
    
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
                'session_id': lead_data.get('session_id', '')
            })
        
        print(f"Lead saved to CSV: {lead_data.get('name', 'Unknown')} ({lead_data.get('email', 'No email')})")
        return True
    except Exception as e:
        print(f"Error saving lead to CSV: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download-guide')
def download_guide():
    """Serve the PDF guide for download"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor
        import io
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#2c3e50'),
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor('#34495e')
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=HexColor('#2c3e50')
        )
        
        # Add title
        story.append(Paragraph("10 LEAD GENERATION STRATEGIES THAT ACTUALLY WORK", title_style))
        story.append(Spacer(1, 20))
        
        # Add introduction
        intro_text = """
        This comprehensive guide will help you implement proven lead generation strategies 
        that will attract qualified prospects and grow your business. Each strategy includes 
        practical tips and actionable steps you can implement immediately.
        """
        story.append(Paragraph(intro_text, body_style))
        story.append(Spacer(1, 20))
        
        # Add strategies
        strategies = [
            {
                "title": "1. CONTENT MARKETING",
                "content": "• Create valuable blog posts, videos, and infographics<br/>• Focus on solving your audience's problems<br/>• Use SEO to attract organic traffic"
            },
            {
                "title": "2. SOCIAL MEDIA ENGAGEMENT",
                "content": "• Build relationships on LinkedIn, Twitter, and Facebook<br/>• Share industry insights and thought leadership<br/>• Engage with potential prospects' content"
            },
            {
                "title": "3. EMAIL MARKETING",
                "content": "• Build targeted email lists<br/>• Create compelling lead magnets<br/>• Use automation for follow-up sequences"
            },
            {
                "title": "4. REFERRAL PROGRAMS",
                "content": "• Incentivize existing customers to refer others<br/>• Create a structured referral process<br/>• Track and reward successful referrals"
            },
            {
                "title": "5. PARTNERSHIPS",
                "content": "• Collaborate with complementary businesses<br/>• Cross-promote each other's services<br/>• Share leads and revenue"
            },
            {
                "title": "6. WEBINARS AND EVENTS",
                "content": "• Host educational webinars<br/>• Attend industry conferences<br/>• Network with potential prospects"
            },
            {
                "title": "7. COLD OUTREACH",
                "content": "• Research and personalize your approach<br/>• Use multiple channels (email, LinkedIn, phone)<br/>• Follow up consistently"
            },
            {
                "title": "8. ACCOUNT-BASED MARKETING",
                "content": "• Target specific high-value accounts<br/>• Create personalized campaigns<br/>• Use multiple touchpoints"
            },
            {
                "title": "9. INFLUENCER MARKETING",
                "content": "• Partner with industry influencers<br/>• Leverage their audience and credibility<br/>• Create mutually beneficial relationships"
            },
            {
                "title": "10. OPTIMIZATION AND TESTING",
                "content": "• A/B test your landing pages<br/>• Optimize your conversion funnel<br/>• Continuously improve based on data"
            }
        ]
        
        for strategy in strategies:
            story.append(Paragraph(strategy["title"], heading_style))
            story.append(Paragraph(strategy["content"], body_style))
            story.append(Spacer(1, 15))
        
        # Add bonus section
        story.append(Spacer(1, 20))
        bonus_heading = Paragraph("BONUS: AI-POWERED LEAD GENERATION", heading_style)
        story.append(bonus_heading)
        
        bonus_content = """
        • Use chatbots for 24/7 lead qualification<br/>
        • Automate follow-up sequences<br/>
        • Personalize content based on behavior<br/>
        • Score leads automatically
        """
        story.append(Paragraph(bonus_content, body_style))
        
        # Add conclusion
        story.append(Spacer(1, 20))
        conclusion_text = """
        <b>Remember:</b> Quality over quantity. Focus on attracting and converting the right prospects for your business.
        
        For more strategies and implementation tips, visit LeadCraft AI at leadcraftai.com
        """
        story.append(Paragraph(conclusion_text, body_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='10_lead_generation_strategies.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return jsonify({'error': 'Error creating PDF'}), 500

@app.route('/', methods=['POST'])
def handle_old_form():
    """Handle old form POST requests and redirect to the new chatbot"""
    return jsonify({
        'response': 'Please use the chat interface to ask questions.',
        'show_email_capture': False
    }), 200

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
        
        # In production, you would:
        # 1. Save to database
        # 2. Send to email service (Mailchimp, ConvertKit, etc.)
        # 3. Send the actual PDF guide
        # 4. Track analytics
        
        print(f"Email captured: {email} from session {session_id}")
        
        return jsonify({'success': True, 'message': 'Email captured successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error capturing email'}), 500

@app.route('/submit_email', methods=['POST'])
def submit_email():
    """Handle email submission for lead magnet"""
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
            'source': 'chatbot_lead_magnet',
            'lead_magnet': '10_lead_generation_strategies_pdf'
        }
        captured_emails.append(email_record)
        
        # In production, you would:
        # 1. Save to database
        # 2. Send to email service (Mailchimp, ConvertKit, etc.)
        # 3. Send the actual PDF guide
        # 4. Track analytics
        
        print(f"Lead magnet email captured: {email} from session {session_id}")
        
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
            'lead_magnet': '10_lead_generation_strategies_pdf'
        }
        
        # Validate required fields
        if not lead_data['name'] or not lead_data['email']:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Store the lead (in production, save to database)
        captured_emails.append(lead_data)
        
        # Save lead to CSV file for Excel compatibility
        csv_saved = save_lead_to_csv(lead_data)
        
        # In production, you would:
        # 1. Save to database
        # 2. Send to CRM (HubSpot, Salesforce, etc.)
        # 3. Send welcome email with PDF guide
        # 4. Track analytics
        # 5. Trigger follow-up sequences
        
        print(f"Lead captured: {lead_data['name']} ({lead_data['email']}) from session {lead_data['session_id']}")
        print(f"Product: {lead_data['product']}")
        print(f"Pain point: {lead_data['pain_point']}")
        print(f"CSV saved: {csv_saved}")
        
        return jsonify({
            'success': True, 
            'message': 'Lead captured successfully',
            'lead_id': f"lead_{len(captured_emails)}",
            'download_link': '/download-guide' # Provide a download link
        })
        
    except Exception as e:
        print(f"Error capturing lead: {e}")
        return jsonify({'success': False, 'message': 'Error capturing lead'}), 500

@app.route('/book-call', methods=['POST'])
def book_call():
    """Handle call booking responses"""
    try:
        data = request.get_json()
        user_response = data.get('response', '').lower()
        
        if 'yes' in user_response or 'book' in user_response or 'call' in user_response:
            return jsonify({
                'success': True,
                'message': 'Great! I\'ve sent the booking link. Please check your email for the calendar invite. Looking forward to our call! 📞',
                'booking_link': 'https://calendly.com/your-calendar/15min-strategy-call'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No worries! If you change your mind, just let me know. I\'m here to help with any questions about lead generation strategies.'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing booking request: {str(e)}'
        }), 500

def check_lead_magnet_trigger(user_message, agent_response):
    """
    Determine if we should offer the lead magnet based on user message and response
    """
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
    """
    Generate contextual suggested questions based on the conversation
    """
    user_lower = user_message.lower()
    response_lower = agent_response.lower()
    
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
    
    elif any(word in user_lower for word in ['ai', 'artificial intelligence', 'machine learning']):
        return [
            "How does the AI work?",
            "Can I train it on my product?",
            "What makes your AI different?"
        ]
    
    # If response mentions lead magnet, suggest related questions
    elif 'pdf' in response_lower or 'guide' in response_lower:
        return [
            "What other resources do you have?",
            "Can I see a demo first?",
            "How do I get started?"
        ]
    
    # Return default suggestions if no specific context
    return default_suggestions[:3]  # Limit to 3 suggestions

@app.route('/captured-emails')
def get_captured_emails():
    """Admin endpoint to view captured emails (for testing)"""
    return jsonify(captured_emails)

@app.route('/dashboard')
def dashboard():
    """Admin dashboard for client management"""
    try:
        # Read leads from CSV file
        leads = []
        csv_file = 'leads.csv'
        
        if os.path.exists(csv_file):
            with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    leads.append(row)
        
        # Sort leads by timestamp (newest first)
        leads.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Calculate some basic stats
        total_leads = len(leads)
        recent_leads = len([lead for lead in leads if lead.get('timestamp', '').startswith('2025-07-20')])
        
        return render_template('dashboard.html', leads=leads, total_leads=total_leads, recent_leads=recent_leads)
        
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        return render_template('dashboard.html', leads=[], total_leads=0, recent_leads=0)

@app.route('/download-leads-csv')
def download_leads_csv():
    """Download leads CSV file for Excel"""
    try:
        csv_file = 'leads.csv'
        
        if not os.path.exists(csv_file):
            # Create empty CSV with headers if file doesn't exist
            fieldnames = ['timestamp', 'name', 'email', 'product', 'pain_point', 'session_id']
            with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
        
        return send_file(
            csv_file,
            as_attachment=True,
            download_name='leads_export.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        print(f"Error downloading CSV: {e}")
        return jsonify({'error': 'Error downloading CSV file'}), 500

if __name__ == '__main__':
    app.run(debug=True)