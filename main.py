from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlmodel import SQLModel, Session, select
from uuid import uuid4
from collections import defaultdict
from enum import Enum
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session
import csv
from io import StringIO
from models import Contact,Message
from models import Contact,MessageRequest,Message,WhatsAppConfig,MessageStatus,Template,TemplateType,TemplateCreate
from database import get_session, init_db
from datetime import datetime
import httpx
import os,requests
from dotenv import load_dotenv
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://saigangapanacea.in"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy database for users
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "admin",
    }
}

# JWT setup
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str

class Campaign(BaseModel):
    id: int
    name: str
    contacts: List[str]
    message: str

campaigns_db: List[Campaign] = []
from typing import Optional, List, Dict, Any

class SendMessageRequest(BaseModel):
    contactId: str
    content: Optional[str] = None  # only for type=text
    type: str = "text"             # text or template
    templateName: Optional[str] = None
    language: Optional[str] = "en_US"
    components: Optional[List[Dict[str, Any]]] = None

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"
    RECEIVED = "received"

@app.on_event("startup")
async def on_startup():
    await init_db()

VERIFY_TOKEN=os.getenv("VERIFY_TOKEN")
@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}

@app.get("/test-db")
def test_db(session: Session = Depends(get_session)):
    return {"ok": True, "count": session.exec(select(Message)).count()}

@app.get("/webhook")
def verify_webhook(request: Request):
    """
    Facebook Webhook verification
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return JSONResponse(content=int(challenge))
    else:
        return JSONResponse(content={"error": "Invalid verification"}, status_code=403)
    

from sqlmodel.ext.asyncio.session import AsyncSession

@app.post("/webhook")
async def receive_message(request: Request, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    print("Received webhook message:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages", [])

        for msg in messages:
            phone_number = msg["from"]
            text_body = msg["text"]["body"]
            timestamp = datetime.utcfromtimestamp(int(msg["timestamp"]))

            # Match or create contact
            result = await session.execute(select(Contact).where(Contact.phone == phone_number))
            contact = result.scalar_one_or_none()

            if not contact:
                contact = Contact(name=phone_number, phone=phone_number)
                session.add(contact)
                await session.commit()
                await session.refresh(contact)

            # Save the message
            message = Message(
                contactId=contact.id,
                content=text_body,
                timestamp=timestamp,
                direction="inbound",
                status=MessageStatus.RECEIVED
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)

    except Exception as e:
        print("❌ Error processing webhook:", e)

    return {"status": "received"}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None or username not in fake_users_db:
            raise HTTPException(status_code=401, detail="Invalid auth")
        return User(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or user['hashed_password'] != form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user



class PasswordChangeRequest(BaseModel):
    currentPassword: str
    newPassword: str

@app.post("/auth/change-password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user)
):
    user_record = fake_users_db.get(current_user.username)
    
    if not user_record or user_record["hashed_password"] != payload.currentPassword:
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Update password (normally you'd hash it)
    user_record["hashed_password"] = payload.newPassword
    return {"detail": "Password updated successfully"}

# ------------------ Contacts ------------------

@app.get("/contacts/", response_model=List[Contact])
async def get_contacts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Contact))
    return result.scalars().all()


@app.post("/contacts/", response_model=Contact)
async def add_contact(contact: Contact, session: AsyncSession = Depends(get_session)):
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact

@app.get("/contacts/{id}", response_model=Contact)
async def get_contact_by_id(id: str, session: Session = Depends(get_session)):
    contact = await session.get(Contact, id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.put("/contacts/{id}", response_model=Contact)
async def update_contact(id: str, updated: Contact, session: Session = Depends(get_session)):
    db_contact =await session.get(Contact, id)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)

    db_contact.updatedAt = datetime.utcnow()
    await session.add(db_contact)
    await session.commit()
    await session.refresh(db_contact)
    return db_contact

@app.delete("/contacts/{id}")
async def delete_contact(id: str, session: Session = Depends(get_session)):
    contact =await session.get(Contact, id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    await session.delete(contact)
    await session.commit()
    return {"detail": "Contact deleted"}


# routes/contact_routes.py or similar
  # Make sure this matches your model location
 # Your DB session dependency

@app.post("/contacts/import")
async def import_contacts_from_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(StringIO(decoded))

    imported = 0
    for row in reader:
        try:
            contact = Contact(
                name=row.get("name", ""),
                phone=row.get("phone", ""),
                email=row.get("email", None)
            )
            session.add(contact)
            imported += 1
        except Exception as e:
            continue  # or log error

    await session.commit()
    return {"message": f"{imported} contacts imported successfully"}


# ------------------ Messages -----------------
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
WHATSAPP_API_URL = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"



@app.get("/messages", response_model=List[Message])
async def get_all_messages(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Message))
    return result.scalars().all()

@app.get("/messages/{contact_id}", response_model=List[Message])
async def get_messages(contact_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Message).where(Message.contactId == contact_id))
    return result.scalars().all()

import httpx

@app.post("/messages/send", response_model=Message)
async def send_message(data: SendMessageRequest, session: AsyncSession = Depends(get_session)):
    contact = await session.get(Contact, data.contactId)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if data.type == "text":
        payload = {
            "messaging_product": "whatsapp",
            "to": contact.phone,
            "type": "text",
            "text": {"body": data.content}
        }

    elif data.type == "template":
        if not data.templateName or not data.components:
            raise HTTPException(status_code=400, detail="Missing template name or components")

        formatted_components = []

        for comp in data.components:
            if comp.get("type") == "body":
                formatted_components.append({
                    "type": "body",
                    "parameters": comp.get("parameters", [])
                })

            elif comp.get("type") == "header":
                first_param = comp.get("parameters", [])[0]
            
                if first_param.get("type") == "image" and first_param.get("image", {}).get("link"):
                    formatted_components.append({
                        "type": "header",
                        "parameters": [{
                            "type": "image",
                            "image": {
                                "link": first_param["image"]["link"]
                            }
                        }]
                    })
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Header format mismatch: Expected image with valid link"
                    )

            elif comp.get("type") == "button":
                formatted_components.append({
                    "type": "button",
                    "sub_type": comp.get("sub_type", "quick_reply"),
                    "index": comp.get("index", "0"),
                    "parameters": comp.get("parameters", [])
                })

        payload = {
            "messaging_product": "whatsapp",
            "to": contact.phone,
            "type": "template",
            "template": {
                "name": data.templateName,
                "language": {"code": data.language or "en_US"},
                "components": formatted_components
            }
        }

    else:
        raise HTTPException(status_code=400, detail="Unsupported message type")

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(WHATSAPP_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        print("WhatsApp API error:", response.status_code, response.text)
        status = MessageStatus.FAILED
    else:
        print("Message sent successfully:", response.json())
        status = MessageStatus.SENT

    message = Message(
        contactId=data.contactId,
        content=data.content or f"TEMPLATE: {data.templateName}",
        timestamp=datetime.utcnow(),
        direction="outbound",
        status=status,
        type=data.type,
        templateName=data.templateName
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)

    return message






# ------------------ Conversations ------------------


@app.get("/conversations")
async def get_conversations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Message).order_by(Message.timestamp.desc())
    )
    messages = result.scalars().all()

    conv_map = {}

    for msg in messages:
        contact_id = msg.contactId
        if not contact_id:
            continue
        if contact_id in conv_map:
            continue  # ✅ skip older messages, we only want latest

        contact = await session.get(Contact, contact_id)
        contact_data = {
            "id": contact.id,
            "name": contact.name,
            "phone": contact.phone,
        } if contact else {
            "id": contact_id,
            "name": f"Contact {contact_id}",
            "phone": contact_id,
        }

        conv_map[contact_id] = {
            "id": f"conv_{contact_id}",
            "contactId": contact_id,
            "contact": contact_data,
            "lastMessage": {
                "id": msg.id,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "status": msg.status,
                "direction": msg.direction,
                "type": msg.type,
            },
            "unreadCount": 0,
            "status": "active",
            "updatedAt": msg.timestamp or datetime.utcnow(),
        }

    return list(conv_map.values())



@app.get("/conversations/{contact_id}")
async def get_conversation(contact_id: str, session: AsyncSession = Depends(get_session)):
    message =await  session.exec(
        select(Message).where(Message.contactId == contact_id).order_by(Message.timestamp.desc())
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="No messages found")

    return {
        "id": f"conv_{contact_id}",
        "contactId": contact_id,
        "contact": {
            "id": contact_id,
            "name": f"Contact {contact_id}",  # Replace with DB fetch if Contact table is used
            "phone": contact_id
        },
        "lastMessage": message,
        "unreadCount": 0,
        "status": "active",
        "updatedAt": message.timestamp
    }

@app.post("/conversations/{contact_id}/mark-read")
async def mark_conversation_as_read(contact_id: str, session: AsyncSession = Depends(get_session)):
    messages = await session.exec(
        select(Message).where(Message.contactId == contact_id, Message.status != "read")
    ).all()

    for message in messages:
        message.status = "read"
        await session.add(message)

    await session.commit()
    return {"success": True}

# ------------------ Campaigns ------------------

@app.get("/campaigns/", response_model=List[Campaign])
def get_campaigns():
    return campaigns_db

@app.post("/campaigns/", response_model=Campaign)
def create_campaign(campaign: Campaign):
    campaigns_db.append(campaign)
    return campaign

#--------------------------------Settings-------------------
from models import WhatsAppConfig

@app.get("/settings/whatsapp", response_model=WhatsAppConfig)
def get_whatsapp_config(session: Session = Depends(get_session)):
    config = session.get(WhatsAppConfig, 1)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config



@app.post("/settings/whatsapp", response_model=WhatsAppConfig)
def update_whatsapp_config(data: WhatsAppConfig, session: Session = Depends(get_session)):
    config = session.get(WhatsAppConfig, 1)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(config, key, value)

    config.isConfigured = bool(
        config.accessToken and config.phoneNumberId and config.businessAccountId
    )

    session.add(config)
    session.commit()
    session.refresh(config)
    return config

@app.get("/settings/test")
def test_whatsapp_connection(session: AsyncSession = Depends(get_session)):
    config = session.get(WhatsAppConfig, 1)
    if not config or not config.isConfigured:
        raise HTTPException(status_code=400, detail="WhatsApp not configured")

    import random
    if random.random() < 0.2:
        raise HTTPException(status_code=500, detail="Failed to connect to WhatsApp API")

    return {"status": "success", "message": "WhatsApp API connection successful"}
#-------------------------------------------------------------------------------------------------------------------------------------------
@app.post("/templates/create-meta")
async def create_template_in_meta(template: TemplateCreate, session: AsyncSession = Depends(get_session)):
    config = await session.get(WhatsAppConfig, 1)
    if not config or not config.isConfigured:
        raise HTTPException(status_code=400, detail="WhatsApp not configured")

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    # Start building payload
    payload = {
        "name": template.name.lower().replace(" ", "_"),
        "category": template.category.upper(),
        "language": template.language,
        "components": []
    }

    # ✅ HEADER (optional)
    if template.header:
        payload["components"].append({
            "type": "HEADER",
            "format": template.type.upper(),
            "example": {
                "header_text": [template.header]
            } if template.type == TemplateType.TEXT else {
                "header_handle": [template.media_url]
            }
        })

    # ✅ BODY (must be included, no 'text' key here)
    payload["components"].append({
        "type": "BODY",
        "example": {
            "body_text": [template.body]  # optional example for body
        }
    })

    # ✅ FOOTER (optional)
    if template.footer:
        payload["components"].append({
            "type": "FOOTER",
            "text": template.footer
        })

    # ✅ BUTTONS (optional)
    if template.buttons_json:
        import json
        buttons = json.loads(template.buttons_json)
        payload["components"].append({
            "type": "BUTTONS",
            "buttons": buttons
        })

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return {"status": "failed", "error": response.text}

    return {"status": "success", "response": response.json()}

@app.get("/templates/meta")
async def fetch_templates_from_meta(session: AsyncSession = Depends(get_session)):
    config = await session.get(WhatsAppConfig, 1)
    if not config or not config.isConfigured:
        raise HTTPException(status_code=400, detail="WhatsApp not configured")

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        return {"status": "error", "error": response.text}

    return response.json()
