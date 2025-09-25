# in orders/services.py

import requests
import re
from django.conf import settings

def send_whatsapp_confirmation(order):
    """
    Sends the WhatsApp confirmation message for a given order,
    including variables for the template.
    """
    api_token = settings.WHATSAPP_API_TOKEN
    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    template_name = settings.WHATSAPP_TEMPLATE_NAME
    
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    customer_phone = re.sub(r'\D', '', order.customer.phone)
    
    # --- MODIFIED PAYLOAD WITH VARIABLES ---
    payload = {
        "messaging_product": "whatsapp",
        "to": customer_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            # This 'components' block is new. It contains the variables.
            "components": [
                {
                    "type": "body", # Or "header" if your variables are in the header
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
                }
            ]
        }
    }
    
    print(f"Sending WhatsApp message to {customer_phone} with variables...")
    
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