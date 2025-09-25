# in orders/services.py

import requests
import re
from django.conf import settings

def send_whatsapp_confirmation(order):
    """
    Sends the WhatsApp confirmation message.
    (This version is for the template with only 2 variables for the brand name).
    """
    api_token = settings.WHATSAPP_API_TOKEN #
    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID #
    template_name = settings.WHATSAPP_TEMPLATE_NAME #
    
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    customer_phone = re.sub(r'\D', '', order.customer.phone) #
    
    # --- PAYLOAD FOR YOUR CURRENT 2-VARIABLE TEMPLATE ---
    payload = {
        "messaging_product": "whatsapp",
        "to": customer_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": order.brand.name # This will replace {{1}}
                        },
                        {
                            "type": "text",
                            "text": order.brand.name # This will replace {{2}}
                        }
                    ]
                },
                # This section sends the unique Order ID back when a button is clicked
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "0",
                    "parameters": [{"type": "payload", "payload": f"confirm_order_{order.id}"}] #
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "1",
                    "parameters": [{"type": "payload", "payload": f"cancel_order_{order.id}"}] #
                }
            ]
        }
    }
    
    print(f"Sending WhatsApp message to {customer_phone} with 2 variables...")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"WhatsApp message sent successfully! Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            print(f"Error sending WhatsApp message: {e}")
            print(f"Response Body: {e.response.text}")
        return False