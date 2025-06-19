from enum import Enum
from datetime import datetime
from typing import Optional,List
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
import uuid

def generate_uuid():
    return str(uuid.uuid4())

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


class Contact(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    phone: str
    email: Optional[str] = None
    #tags: Optional[str] = Field(default="")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    lastMessageAt: Optional[datetime] = None

class Message(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    contactId: str = Field(foreign_key="contact.id")
    content: str
    type: MessageType = MessageType.TEXT
    direction: MessageDirection = MessageDirection.OUTBOUND
    status: MessageStatus = MessageStatus.SENT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
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
