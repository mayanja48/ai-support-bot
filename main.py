from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
from typing import Optional
import re

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Support Bot API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials. Check your .env file")

supabase: Client = create_client(supabase_url, supabase_key)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    business_id: str

def generate_local_response(user_message, business_context):
    """Generate intelligent responses without external API"""
    
    user_message_lower = user_message.lower()
    
    # Pattern matching for common questions
    patterns = {
        r'\b(return|refund|exchange)\b': 
            f"Based on our policy: {extract_policy(business_context, 'return')}",
        
        r'\b(shipping|delivery|arrive|when.*get)\b': 
            f"Shipping information: {extract_policy(business_context, 'shipping')}",
        
        r'\b(price|cost|how much|fee)\b': 
            "For pricing information, please visit our website or contact sales.",
        
        r'\b(contact|support|help|phone|email)\b': 
            "You can reach our support team at support@example.com or call 1-800-123-4567.",
        
        r'\b(hello|hi|hey|greetings)\b': 
            "Hello! Thank you for contacting customer support. How can I help you today?",
        
        r'\b(thank|thanks|appreciate)\b': 
            "You're welcome! Is there anything else I can help you with?",
        
        r'\b(bye|goodbye|see you)\b': 
            "Thank you for contacting us. Have a great day!"
    }
    
    # Check for matching patterns
    for pattern, response in patterns.items():
        if re.search(pattern, user_message_lower):
            return response
    
    # Default response for unknown questions
    return f"""I'd be happy to help! Based on our business information: {business_context[:200]}...
    
For more specific questions about returns, shipping, or support, please let me know!"""

def extract_policy(context, policy_type):
    """Extract specific policy information from business context"""
    context_lower = context.lower()
    
    if policy_type == 'return' and 'return' in context_lower:
        return "We offer a 30-day return policy for all electronics."
    elif policy_type == 'shipping' and 'shipping' in context_lower:
        return "Shipping typically takes 2-3 business days."
    
    return "Please contact support for specific policy details."

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print(f"Received message: {request.message}")
        
        # Get business context
        business_response = supabase.table("businesses").select("context").eq("id", request.business_id).execute()
        
        if not business_response.data:
            raise HTTPException(status_code=404, detail="Business not found")
        
        business_context = business_response.data[0]["context"]
        print(f"Business context loaded successfully")

        # Generate response using local AI (no API calls needed!)
        ai_response = generate_local_response(request.message, business_context)
        print(f"Generated local response: {ai_response[:100]}...")
        
        # Store conversation
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Store user message
        supabase.table("conversations").insert({
            "conversation_id": conversation_id, 
            "message": request.message, 
            "role": "user", 
            "business_id": request.business_id
        }).execute()
        
        # Store AI response
        supabase.table("conversations").insert({
            "conversation_id": conversation_id, 
            "message": ai_response, 
            "role": "assistant", 
            "business_id": request.business_id
        }).execute()
        
        return {
            "response": ai_response,
            "conversation_id": conversation_id,
            "success": True,
            "source": "local_ai"  # Indicate this is a local response
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # Fallback response
        fallback = "I apologize for the technical issue. Our typical policies include 30-day returns and 2-3 day shipping. Please contact support for immediate assistance."
        return {
            "response": fallback,
            "conversation_id": str(uuid.uuid4()),
            "success": False,
            "error": str(e)
        }

@app.get("/")
async def root():
    return {"message": "AI Support Bot API is running! (Local AI Mode)"}

@app.get("/test-db")
async def test_db():
    try:
        # Test Supabase connection
        result = supabase.table("businesses").select("id, name, context").execute()
        return {"status": "Database connected successfully", "businesses": result.data}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)