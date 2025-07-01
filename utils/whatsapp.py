# utils/whatsapp.py
import httpx
import os

WHATSAPP_CLOUD_API_URL = f"https://graph.facebook.com/v19.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")

async def send_whatsapp_template(to_number: str, template_name: str, language_code: str, components: list = None):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }

    if components:
        payload["template"]["components"] = components

    async with httpx.AsyncClient() as client:
        response = await client.post(WHATSAPP_CLOUD_API_URL, json=payload, headers=headers)
        return response
