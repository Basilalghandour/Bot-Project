# in orders/services.py

import requests
import re # Import the regular expression module
from django.conf import settings

def send_whatsapp_confirmation(order):
    """
    Sends the WhatsApp confirmation message for a given order.
    """
    api_token = settings.WHATSAPP_API_TOKEN
    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    template_name = settings.WHATSAPP_TEMPLATE_NAME
    
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    # --- THIS IS THE FIX ---
    # Sanitize the phone number to remove any non-digit characters (+, -, etc.)
    customer_phone = re.sub(r'\D', '', order.customer.phone)
    
    # Simplified payload without the 'components' section
    payload = {
        "messaging_product": "whatsapp",
        "to": customer_phone, # Use the cleaned phone number
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
        }
    }
    
    print(f"Sending WhatsApp message to {customer_phone}...")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"WhatsApp message sent successfully! Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending WhatsApp message: {e}")
        # Now that we're getting a proper error, let's try to print the body again
        if e.response is not None:
            print(f"Response Body: {e.response.text}")
        return False