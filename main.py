import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import httpx
import time
import os

from config import settings
from database import get_db, UserTokenStore
from clients.zoho_client import ZohoClient
from ai.graph import compiled_agent_graph # Note: Ensure this matches your compiled variable name (e.g., compiled_agent_graph)
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

app = FastAPI(title="Zoho LangGraph Chatbot Backend")

# Enable CORS for effortless browser communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicitly required scope list per assignment rules
ZOHO_SCOPES = [
    "ZohoProjects.portals.READ",
    "ZohoProjects.projects.READ",
    "ZohoProjects.tasks.READ",
    "ZohoProjects.tasks.CREATE",
    "ZohoProjects.tasks.UPDATE",
    "ZohoProjects.tasks.DELETE"
]

# ==========================================================
# NEW ENDPOINT: SERVE HTML UI
# ==========================================================
@app.get("/", response_class=HTMLResponse)
def serve_homepage():
    """Serves the front-end chat interface directly from the templates folder."""
    try:
        with open(os.path.join("templates", "index.html"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h2>Welcome to Zoho AI Project Assistant Backend!</h2>
        <p>Frontend file not found. Please ensure <code>templates/index.html</code> exists.</p>
        <p><a href="/auth/login">Click here to Authenticate with Zoho OAuth first</a></p>
        """

@app.get("/auth/login")
def auth_login():
    """Builds authorization url pointing to remote Zoho authentication nodes."""
    scope_string = ",".join(ZOHO_SCOPES)
    authorization_url = (
        f"{settings.ZOHO_ACCOUNTS_URL}/oauth/v2/auth"
        f"?scope={scope_string}"
        f"&client_id={settings.ZOHO_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={settings.ZOHO_REDIRECT_URI}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(url=authorization_url)

@app.get("/auth/callback")
async def auth_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Receives code token payload to execute permanent credentials transaction."""
    token_payload = {
        "code": code,
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "redirect_uri": settings.ZOHO_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{settings.ZOHO_ACCOUNTS_URL}/oauth/v2/token", params=token_payload)
        token_data = response.json()
        
        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail=f"OAuth verification aborted: {token_data}")
            
        target_user_id = "demo_user_123"
        
        user_record = db.query(UserTokenStore).filter(UserTokenStore.user_id == target_user_id).first()
        if not user_record:
            user_record = UserTokenStore(user_id=target_user_id)
            db.add(user_record)
            
        user_record.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            user_record.refresh_token = token_data["refresh_token"]
            
        user_record.expires_at = int(time.time()) + int(token_data.get("expires_in", 3600))
        db.commit()

    # Automatically redirect back to the home chat interface after successful login!
    return RedirectResponse(url="/")

class ChatRequest(BaseModel):
    user_input: str
    user_id: str = "demo_user_123"
    session_id: str = "global_session_001"
    confirm_action: bool = False
    decline_action: bool = False

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.session_id}}
    
    if request.confirm_action:
        compiled_agent_graph.update_state(config, {"action_approved": True})
        response_state = compiled_agent_graph.invoke(None, config)
        return {"response": response_state["messages"][-1].content, "requires_hil": False}
        
    if request.decline_action:
        compiled_agent_graph.update_state(config, {"next_action_pending": None, "action_approved": False})
        return {"response": "❌ Operation safely cancelled by the user.", "requires_hil": False}

    initial_inputs = {
        "messages": [HumanMessage(content=request.user_input)],
        "user_id": request.user_id,
        "action_approved": False
    }
    
    output_state = compiled_agent_graph.invoke(initial_inputs, config)
    last_bot_reply = output_state["messages"][-1].content
    is_hil_waiting = output_state.get("next_action_pending") is not None
    
    return {
        "response": last_bot_reply,
        "requires_hil": is_hil_waiting
    }
class EmailRequest(BaseModel):
    target_email: str
    report_content: str
    subject: str = "Skysecure Zoho Assistant - Generated Report"

@app.post("/send-email")
async def send_email_report(request: EmailRequest):
    try:
        # Create the email package
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_EMAIL
        msg['To'] = request.target_email
        msg['Subject'] = request.subject

        # Attach the report content (you can format this as HTML or plain text)
        msg.attach(MIMEText(request.report_content, 'plain'))

        # Connect to Google's SMTP server securely
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        
        # Dispatch and close
        server.send_message(msg)
        server.quit()
        
        return {"status": "success", "message": f"Report securely delivered to {request.target_email}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch email: {str(e)}")
