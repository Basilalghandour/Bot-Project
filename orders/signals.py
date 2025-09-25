# in orders/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .services import send_whatsapp_confirmation

@receiver(post_save, sender=Order)
def send_confirmation_on_order_create(sender, instance, created, **kwargs):
    """
    Listens for a new Order instance being created and triggers the WhatsApp message.
    """
    # The 'created' flag is True only when the record is first created
    if created:
        print(f"Signal received: New order {instance.id} created. Triggering WhatsApp message.")
        send_whatsapp_confirmation(instance)