import os
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
        docs = f.read().split("\n\n")
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
    """Analyze if this is a qualified lead"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a lead qualification expert. Analyze if the user shows buying intent. Return only 'qualified' or 'not_qualified'."},
                {"role": "user", "content": f"User message: {user_input}"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        return response.choices[0].message.content.strip().lower()
    except:
        return "not_qualified"

def generate_follow_up(user_input, session_id):
    """Generate contextual follow-up questions"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sales assistant. Generate 1-2 relevant follow-up questions to continue the conversation naturally. Keep them short and specific."},
                {"role": "user", "content": f"User said: {user_input}\n\nGenerate follow-up questions:"}
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
            "guide_offered": False,
            "call_offered": False
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
    
    # Qualify the lead
    is_qualified = qualify_lead(user_input, session_id)
    if is_qualified == "qualified":
        conversation_history[session_id]["lead_score"] += 1
    
    # Generate response with context
    try:
        # Build conversation context
        recent_messages = conversation_history[session_id]["messages"][-3:]  # Last 3 messages
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
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
        if conversation_history[session_id]["lead_score"] >= 2 and not conversation_history[session_id]["guide_offered"]:
            main_response += "\n\n📚 **Free Guide**: I'd love to send you our comprehensive guide on lead generation strategies. It's packed with actionable tips that have helped our clients double their leads in 30 days. Would you like me to send it to your email?"
            conversation_history[session_id]["guide_offered"] = True
        
        # Offer call booking if guide was offered and call not yet offered
        elif conversation_history[session_id]["guide_offered"] and not conversation_history[session_id]["call_offered"]:
            main_response += "\n\n📞 **Free Strategy Call**: I'd love to hop on a quick 15-minute call to discuss your specific lead generation challenges and share some personalized strategies. No sales pitch - just pure value! Here's my booking link: https://calendly.com/your-calendar/15min-strategy-call"
            conversation_history[session_id]["call_offered"] = True
        
        # Generate follow-up if lead is qualified
        follow_up = ""
        if conversation_history[session_id]["lead_score"] >= 2 and not conversation_history[session_id]["guide_offered"]:
            follow_up = generate_follow_up(user_input, session_id)
            if follow_up:
                main_response += f"\n\n{follow_up}"
        
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": main_response})
        return main_response
        
    except Exception as e:
        # Fallback to direct FAQ response
        fallback_response = faq_context if faq_context != "Sorry, I couldn't find an answer for that." else "I'd be happy to help! Could you tell me more about what you're looking for?"
        conversation_history[session_id]["messages"].append({"role": "assistant", "content": fallback_response})
        return fallback_response
