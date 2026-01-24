# LeadCraft AI - Complete Tutorial

## Overview
LeadCraft AI is a lead generation and qualification platform that uses AI-powered chatbots to capture and qualify leads. This tutorial focuses on building a streamlined system for lead qualification, scoring, and CSV storage.

**Core Features:**
- Flask web application with AI chatbot
- OpenAI GPT-3.5 integration for intelligent responses
- ChromaDB for semantic search of FAQ content
- Lead capture and qualification system
- Lead scoring and CSV storage
- Modern responsive UI with CSS

## Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Basic knowledge of Python, HTML, CSS, and JavaScript
- Git (optional but recommended)

## Project Structure
```
LeadCraft-AI/
├── app.py                 # Main Flask application
├── agent.py              # AI agent logic
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── faq.txt              # FAQ content for semantic search
├── lead_generation_guide.txt  # Lead magnet content
├── leads.csv            # Lead storage (auto-generated)
├── static/
│   └── style.css        # Landing page styles
└── templates/
    └── index.html       # Landing page
```

## Step 1: Project Setup

### 1.1 Create Project Directory
```bash
mkdir LeadCraft-AI
cd LeadCraft-AI
```

### 1.2 Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies
```bash
pip install flask openai chromadb python-dotenv
```

### 1.4 Create requirements.txt
```bash
pip freeze > requirements.txt
```

## Step 2: Environment Configuration

### 2.1 Create .env File
Create a `.env` file in your project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 2.2 Get OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

## Step 3: Core Application Files

### 3.1 Create app.py (Main Flask Application)
This is the main Flask application that handles:
- Web routes and endpoints
- Lead capture and storage
- CSV file management

Key features:
- `/` - Landing page with chatbot
- `/ask` - AI chatbot endpoint
- `/capture-email` - Email capture for lead magnets
- `/submit_lead` - Lead qualification and capture

### 3.2 Create agent.py (AI Agent Logic)
This file contains the AI agent that:
- Integrates with OpenAI GPT-3.5
- Manages conversation history
- Qualifies leads using AI
- Searches FAQ content using ChromaDB
- Generates contextual responses

Key functions:
- `run_agent()` - Main agent function
- `qualify_lead()` - AI-powered lead qualification
- `search_docs()` - Semantic search in FAQ
- `generate_follow_up()` - Contextual follow-up questions

## Step 4: Content Files

### 4.1 Create faq.txt
This file contains FAQ content that the AI uses for semantic search:
```
What is LeadCraft AI?
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
```

### 4.2 Create lead_generation_guide.txt
This contains the content for your lead magnet:
```
10 LEAD GENERATION STRATEGIES THAT ACTUALLY WORK

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
```

## Step 5: Frontend Development

### 5.1 Create templates/index.html (Landing Page)
This is the main landing page featuring:
- Hero section with value proposition
- AI chatbot interface
- Lead capture forms
- Modern responsive design

Key components:
- Chatbot container with message history
- Email capture modal for lead magnets
- Lead qualification form
- Suggested questions feature

### 5.2 Create static/style.css (Landing Page Styles)
Modern CSS styling for the landing page:
- Responsive design
- Modern color scheme
- Smooth animations
- Mobile-friendly layout
- Professional typography

## Step 6: AI Integration

### 6.1 OpenAI Integration
The AI agent uses OpenAI's GPT-3.5-turbo model for:
- Natural language understanding
- Contextual responses
- Lead qualification
- Follow-up question generation

### 6.2 ChromaDB Integration
ChromaDB provides semantic search capabilities:
- Stores FAQ content as embeddings
- Enables intelligent content retrieval
- Improves response accuracy
- Supports conversation context

### 6.3 Lead Qualification Logic
The system qualifies leads based on:
- Buying intent indicators
- Engagement level
- Conversation quality
- Specific keywords and phrases

## Step 7: Lead Management System

### 7.1 Lead Capture Flow
1. User interacts with chatbot
2. AI qualifies the lead
3. Lead information is captured
4. Data is stored in CSV file
5. Lead score is calculated

### 7.2 Lead Storage
- CSV file for simple storage
- JSON format for flexibility
- Timestamp tracking
- Session management

### 7.3 CSV Structure
The leads.csv file contains:
- timestamp: When the lead was captured
- name: Lead's name
- email: Lead's email address
- product: Product/service they're interested in
- pain_point: Their main challenge
- session_id: Chat session identifier
- lead_score: AI-calculated qualification score

## Step 8: Testing and Deployment

### 8.1 Local Testing
```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python app.py

# Access the application
# Landing page: http://127.0.0.1:5000
```

### 8.2 Testing Checklist
- [ ] Chatbot responds to questions
- [ ] Email capture works
- [ ] Lead qualification functions
- [ ] CSV file is created and updated
- [ ] Lead scoring works correctly
- [ ] Mobile responsiveness
- [ ] Error handling

### 8.3 Production Deployment
For production deployment, consider:
- Using a production WSGI server (Gunicorn)
- Setting up a proper database (PostgreSQL)
- Implementing email service integration
- Adding SSL certificates
- Setting up monitoring and logging

## Step 9: Advanced Features

### 9.1 Email Integration
Integrate with email services like:
- SendGrid
- Mailchimp
- ConvertKit
- ActiveCampaign

### 9.2 CRM Integration
Connect with popular CRMs:
- HubSpot
- Salesforce
- Pipedrive
- Zoho CRM

### 9.3 Analytics and Tracking
Add analytics features:
- Lead source tracking
- Conversion rates
- Chatbot performance metrics
- User behavior analysis

## Common Issues and Solutions

### Issue 1: OpenAI API Key Error
**Problem**: "Invalid API key" error
**Solution**: 
1. Check your `.env` file has the correct API key
2. Ensure the key is active in your OpenAI account
3. Verify you have sufficient credits

### Issue 2: ChromaDB Connection Error
**Problem**: ChromaDB collection creation fails
**Solution**:
1. Ensure ChromaDB is properly installed
2. Check file permissions for the project directory
3. Restart the application

### Issue 3: CSS Not Loading
**Problem**: Styles not appearing on the page
**Solution**:
1. Check the CSS file paths in HTML
2. Ensure Flask static file serving is working
3. Clear browser cache

### Issue 4: CSV Not Saving
**Problem**: Lead data not being saved to CSV
**Solution**:
1. Check file permissions for the project directory
2. Ensure the CSV file path is correct
3. Verify the data format is correct

## Best Practices

### 1. Security
- Never commit API keys to version control
- Use environment variables for sensitive data
- Implement proper input validation
- Add rate limiting for API endpoints

### 2. Performance
- Optimize database queries
- Implement caching where appropriate
- Use async operations for external API calls
- Monitor application performance

### 3. User Experience
- Provide clear error messages
- Implement loading states
- Ensure mobile responsiveness
- Test across different browsers

### 4. Code Organization
- Separate concerns (MVC pattern)
- Use meaningful variable names
- Add comments for complex logic
- Follow PEP 8 style guidelines

## Next Steps

After completing this tutorial, consider:

1. **Adding Authentication**: Implement user login for the dashboard
2. **Database Integration**: Replace CSV storage with a proper database
3. **Email Automation**: Set up automated email sequences
4. **Advanced AI Features**: Implement sentiment analysis and intent detection
5. **Multi-language Support**: Add internationalization
6. **API Development**: Create REST API for mobile apps
7. **Advanced Analytics**: Implement detailed reporting and insights

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)

## Conclusion

Congratulations! You've successfully built a complete AI-powered lead generation platform focused on qualification and scoring. This project demonstrates modern web development practices, AI integration, and lead management systems. Use this foundation to build more advanced features and scale your application.

Remember to:
- Keep your dependencies updated
- Monitor your OpenAI API usage
- Regularly backup your lead data
- Test new features thoroughly
- Gather user feedback for improvements

Happy coding! 🚀 