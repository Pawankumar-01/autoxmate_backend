from fastapi import HTTPException
from models import WhatsAppConfig, Contact
from database import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import httpx
import os
from dotenv import load_dotenv
import copy
import json

load_dotenv()

WHATSAPP_CLOUD_API_URL = f"https://graph.facebook.com/v19.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")


async def send_template_message(
    session: AsyncSession,
    template_name: str,
    language: str,
    components: list,
    contact_ids: list[str]
):
    # ✅ Check WhatsApp configuration
    print("📨 Calling send_template_message")
    config = await session.get(WhatsAppConfig, 1)
    if not config or not config.isConfigured:
        raise HTTPException(status_code=400, detail="WhatsApp not configured")

    # ✅ Fetch actual phone numbers from contact_ids
    result = await session.exec(select(Contact).where(Contact.id.in_(contact_ids)))
    contacts = result.all()
    phone_numbers = [c.phone for c in contacts if c.phone]

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    for phone in phone_numbers:
        local_components = copy.deepcopy(components)
        cleaned_components = []
        skip_message = False

        for comp in local_components:
            comp_type = comp.get("type")

            if comp_type == "header":
                params = comp.get("parameters", [])
                if params and params[0].get("type") == "image":
                    image_link = params[0]["image"].get("link", "")
                    if image_link.startswith("data:image"):
                        print(f"⚠️ Skipping contact {phone}: base64 image not allowed")
                        skip_message = True
                        break
                cleaned_components.append(comp)

            elif comp_type == "body":
                cleaned_components.append(comp)

            elif comp_type == "button":
                sub_type = comp.get("sub_type")
                index = comp.get("index")
                print(f"🧩 Button at index {index} has sub_type: {sub_type}")

                if sub_type == "url":
                    # ❌ Meta does not allow sending URL buttons in payload
                    print(f"🚫 Skipping 'url' button at index {index} — not allowed in payload.")
                    continue

                elif sub_type == "quick_reply":
                    params = comp.get("parameters", [])
                    if not params:
                        comp["parameters"] = [{
                            "type": "payload",
                            "payload": f"reply_{index}"
                        }]
                    cleaned_components.append(comp)

        if skip_message:
            continue

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": { "code": language },
                "components": cleaned_components
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(WHATSAPP_CLOUD_API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"❌ Failed to send to {phone}: {response.text}")
        else:
            print(f"✅ Sent to {phone}: {response.text}")

        # 🧾 Debug
        print("📨 Payload:", json.dumps(payload, indent=2))
        print("🔁 Response:", response.status_code, response.text)
        print("🧹 Final components for message:")
        print(json.dumps(cleaned_components, indent=2))
