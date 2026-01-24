# LeadCraft AI - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Use the Project Generator (Recommended)

1. **Run the generator script:**
   ```bash
   python generate_project.py
   ```

2. **Navigate to the project:**
   ```bash
   cd LeadCraft-AI
   ```

3. **Set up your environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Add your OpenAI API key:**
   - Edit the `.env` file
   - Replace `your_openai_api_key_here` with your actual API key

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Open your browser:**
   - Landing page: http://127.0.0.1:5000

### Option 2: Manual Setup

1. **Create project directory:**
   ```bash
   mkdir LeadCraft-AI
   cd LeadCraft-AI
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install flask openai chromadb python-dotenv
   ```

4. **Create .env file:**
   ```bash
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

5. **Copy project files:**
   - Copy `app.py`, `agent.py` from the original project
   - Copy `templates/` and `static/` directories
   - Copy `faq.txt` and `lead_generation_guide.txt`

6. **Run the application:**
   ```bash
   python app.py
   ```

## 🔑 Getting Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

## 🧪 Testing the Application

1. **Test the chatbot:**
   - Go to http://127.0.0.1:5000
   - Ask questions like "What is LeadCraft AI?" or "How much does it cost?"
   - The AI should respond intelligently

2. **Test lead capture:**
   - Ask about pricing or lead generation
   - The system should offer a free guide
   - Enter an email to test capture

3. **Test lead qualification:**
   - Ask questions that show buying intent
   - The AI should qualify the lead and assign a score
   - Check the `leads.csv` file for captured data

4. **Check CSV output:**
   - Look for `leads.csv` file in your project directory
   - Verify lead data is being saved correctly
   - Check that lead scores are being calculated

## 🐛 Common Issues

### "Invalid API key" error
- Check your `.env` file has the correct API key
- Ensure the key is active in your OpenAI account
- Verify you have sufficient credits

### "Module not found" errors
- Make sure you're in the virtual environment
- Run `pip install -r requirements.txt`
- Check all dependencies are installed

### CSS not loading
- Ensure Flask static file serving is working
- Check CSS file paths in HTML templates
- Clear browser cache

### CSV not saving
- Check file permissions for the project directory
- Ensure the CSV file path is correct
- Verify the data format is correct

## 📊 Understanding Lead Scoring

The system automatically scores leads based on:
- **Buying intent indicators** (pricing, cost, plan, demo)
- **Engagement level** (conversation length, questions asked)
- **Conversation quality** (specific vs general questions)
- **Keywords** (interested, looking for, need help)

Lead scores range from 0-10, where:
- 0-3: Low interest
- 4-6: Moderate interest
- 7-10: High interest/qualified

## 📚 Next Steps

After getting the basic application running:

1. **Read the full tutorial:** `TUTORIAL.md`
2. **Customize the FAQ:** Edit `faq.txt`
3. **Update the lead magnet:** Modify `lead_generation_guide.txt`
4. **Style your application:** Update CSS files
5. **Add your own features:** Extend the functionality

## 🆘 Need Help?

- Check the full tutorial in `TUTORIAL.md`
- Review the code comments in `app.py` and `agent.py`
- Test each component individually
- Check the browser console for JavaScript errors
- Verify the `leads.csv` file is being created and updated

Happy coding! 🎉 