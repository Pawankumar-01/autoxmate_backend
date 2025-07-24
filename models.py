from enum import Enum
<<<<<<< HEAD
from datetime import datetime,timezone
=======
from datetime import datetime
>>>>>>> 49910982bd3026b0204d439985cb8a193f8e604d
from typing import Optional,List,Dict,Any
from pydantic import BaseModel
from sqlmodel import SQLModel, Field,Column,JSON
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# ------------------- ENUMS -------------------

class MessageType(str, Enum):
    TEXT = "text"
    TEMPLATE = "template"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"
    RECEIVED = "received"

class SendMessageRequest(BaseModel):
    contactId: str
    content: str

# ------------------- MODELS -------------------

class Contact(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    phone: str
    email: Optional[str] = None
<<<<<<< HEAD
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
=======
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
>>>>>>> 49910982bd3026b0204d439985cb8a193f8e604d
    lastMessageAt: Optional[datetime] = None

class Message(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    contactId: str = Field(foreign_key="contact.id")
    content: str
    type: MessageType = Field(default=MessageType.TEXT)
    direction: MessageDirection = Field(default=MessageDirection.OUTBOUND)
    status: MessageStatus = Field(default=MessageStatus.SENT)
<<<<<<< HEAD
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))    
=======
    timestamp: datetime = Field(default_factory=datetime.utcnow)
>>>>>>> 49910982bd3026b0204d439985cb8a193f8e604d
    templateName: Optional[str] = None

class MessageRequest(BaseModel):
    to: str
    message: str
    type: str
    templateName: Optional[str] = None

class WhatsAppConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    accessToken: str
    phoneNumberId: str
    businessAccountId: str
    webhookUrl: Optional[str] = None
    webhookToken: Optional[str] = None
    isConfigured: bool = False





class TemplateType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"

class ButtonType(str, Enum):
    URL = "url"
    CALL = "call"
    QUICK_REPLY = "quick_reply"

class Template(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    category: str = "MARKETING"  # or TRANSACTIONAL
    language: str = "en_US"
    header: Optional[str] = None
    body: str
    footer: Optional[str] = None
    type: TemplateType = TemplateType.TEXT
    media_url: Optional[str] = None
    buttons_json: Optional[str] = None  # stored as JSON string
<<<<<<< HEAD
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
=======
    createdAt: datetime = Field(default_factory=datetime.utcnow)
>>>>>>> 49910982bd3026b0204d439985cb8a193f8e604d



class TemplateCreate(BaseModel):
    name: str
    category: str
    language: str
    header: Optional[str] = None
    body: str
    footer: Optional[str] = None
    type: Optional[str] = "text"
    media_url: Optional[str] = None
    buttons_json: Optional[str] = None
    components: Optional[List[Dict[str, Any]]] = None

class SendMessageRequest(BaseModel):
    contactId: str
    content: Optional[str] = None  # Only for type='text'
    type: str = "text"             # "text" or "template"
    templateName: Optional[str] = None
    language: Optional[str] = "en_US"
    components: Optional[List[Dict[str, Any]]] = None


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template_id: str
    template_name: str
    components: List[Dict[str, Any]]
    contact_ids: List[str]
    scheduled_at: Optional[datetime] = None
    created_by: str

class Campaign(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    description: Optional[str] = None
    template_id: str
    template_name: str
    language: str = "en_US"
    
    # Store lists/dicts as JSON
    components: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    contact_ids: List[str] = Field(sa_column=Column(JSON))

    scheduled_at: Optional[datetime] = None
    created_by: str
<<<<<<< HEAD
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
=======
    created_at: datetime = Field(default_factory=datetime.utcnow)
>>>>>>> 49910982bd3026b0204d439985cb8a193f8e604d
    run_payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    status: Optional[str] = Field(default="draft")