from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, render
from.adapters import adapt_incoming_order
from .models import *
from .serializers import *
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json



class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    lookup_field = "webhook_id"
    lookup_value_regex = "[0-9a-f-]{32}"  # UUID regex


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        brand_webhook_id = self.kwargs.get("brand_webhook_id")
        if brand_webhook_id:
            brand = get_object_or_404(Brand, webhook_id=brand_webhook_id)
            return Order.objects.filter(brand=brand)
        return Order.objects.all()

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        try:
            print("=== WEBHOOK REQUEST START ===")
            print("METHOD:", request.method)
            print("PATH:", request.path)
            print("CONTENT_TYPE:", request.content_type)
            headers = {k: v for k, v in request.META.items() if k.startswith("HTTP_")}
            print("HEADERS:", json.dumps(headers, indent=2)[:2000])
            print("RAW BODY:", request.body[:500])
            print("request.data preview:", json.dumps(request.data, indent=2) if request.data else None)
            print("=== WEBHOOK REQUEST END ===")
        except Exception as e:
            print("Error logging request:", e)

        # ---- Handle GET/HEAD (reachability ping) ----
        if request.method != "POST":
            return Response({"detail": "ok - ping (non-POST)"}, status=status.HTTP_200_OK)

        # ---- Parse payload ----
        payload = request.data or {}

        # ---- Define what real orders look like ----
        order_keys = {"line_items", "billing", "customer", "items", "order_key", "total"}

        # ---- Detect WooCommerce "test ping" ----
        if not any(key in payload for key in order_keys):
            # Example: {"webhook_id": "1"}
            return Response({"detail": "ok - webhook test/handshake"}, status=status.HTTP_200_OK)

     
        
        brand_webhook_id = self.kwargs.get("brand_webhook_id")
        brand = None

        if brand_webhook_id:
            brand = get_object_or_404(Brand, webhook_id=brand_webhook_id)
        else:
            domain = request.data.get("store_domain") or request.data.get("meta_data", [{}])[0].get("value")
            if domain:
                brand = Brand.objects.filter(website__icontains=domain).first()

        # Normalize payload
        adapted = adapt_incoming_order(request.data, brand=brand)
        customer_data = adapted.pop("customer", {})

        # Create or get Customer instance
        customer = Customer.objects.create(
                 first_name = customer_data.get("first_name", ""),
                 last_name = customer_data.get("last_name", ""),
                 email = customer_data.get("email", ""),
                 phone = customer_data.get("phone", ""),
                 address = customer_data.get("address", ""),
                 apartment = customer_data.get("apartment", ""),
                 city = customer_data.get("city", ""),
                 state = customer_data.get("state", ""),
                 country = customer_data.get("country", ""),
                 postal_code = customer_data.get("postal_code", ""),
            
        )

        # Pass customer instance via context
        serializer = self.get_serializer(data=adapted, context={'customer': customer})
        serializer.is_valid(raise_exception=True)
        order = serializer.save(brand=brand)

        out_serializer = self.get_serializer(order)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)            

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()


class CustomerOrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        customer_id = self.kwargs.get("customer_pk")
        get_object_or_404(Customer, pk=customer_id)
        return Order.objects.filter(customer_id=customer_id)    

class ConfirmationViewSet(viewsets.ModelViewSet):
    queryset = Confirmation.objects.all()
    serializer_class = ConfirmationSerializer


# in your views.py file

class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        # Get webhook_id from URL
        webhook_id = self.kwargs.get('brand_webhook_id')      

        # Find the brand or return 404 if not found
        brand = get_object_or_404(Brand, webhook_id=webhook_id)

        # Get all orders for this brand
        orders = Order.objects.filter(brand=brand).order_by('-created_at')

        # --- ADD THIS SECTION ---
        # Calculate the metrics from the orders queryset
        metrics = {
            'total_orders': orders.count(),
            'confirmed': orders.filter(status='confirmed').count(),
            'pending': orders.filter(status='pending').count(),
            'cancelled': orders.filter(status='cancelled').count(),
        }
        # --- END OF NEW SECTION ---

        # Pass brand, orders, and the new metrics into the template context
        context = {
            "brand": brand,
            "orders": orders,
            "metrics": metrics, # Add the metrics dictionary here
        }

        return render(request, "dashboard.html", context)
    
    
    
    
# in orders/views.py

# Add these imports at the top of the file
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import json
# The Order model is already imported via 'from .models import *'

# Add this new function at the end of the file
# in orders/views.py

# in orders/views.py

@csrf_exempt
def whatsapp_webhook(request):
    # ... (the GET request handler is the same)
    if request.method == "GET":
        verify_token = settings.WHATSAPP_VERIFY_TOKEN
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == verify_token:
            print("WEBHOOK_VERIFIED")
            return HttpResponse(challenge, status=200)
        else:
            print("WEBHOOK_VERIFICATION_FAILED")
            return HttpResponse("error, verification failed", status=403)

    if request.method == "POST":
        data = json.loads(request.body)
        print("--- WHATSAPP WEBHOOK RECEIVED ---")
        print(json.dumps(data, indent=2))

        if "object" in data and data.get("object") == "whatsapp_business_account":
            try:
                message = data["entry"][0]["changes"][0]["value"]["messages"][0]
                
                # --- THIS IS THE CORRECTED LOGIC ---
                # Check for message type "button" instead of "interactive"
                if message.get("type") == "button":
                    # Get the payload from the correct location
                    button_payload = message["button"]["payload"]
                    print(f"DEBUG: Button payload received: {button_payload}")

                    action, _, order_id = button_payload.partition('_order_')

                    try:
                        print(f"DEBUG: Attempting to find Order with ID: {order_id}")
                        order = Order.objects.get(id=int(order_id))
                        print(f"DEBUG: Found Order {order_id}. Current status is: '{order.status}'")
                        
                        if order.status == 'pending':
                            print("DEBUG: Order status is 'pending'. Proceeding to update.")
                            if action == "confirm":
                                order.status = "confirmed"
                            elif action == "cancel":
                                order.status = "cancelled"
                            
                            order.save()
                            print(f"DEBUG: Order {order_id} saved. New status is: '{order.status}'")
                        else:
                            print(f"DEBUG: Ignoring duplicate reply for Order {order_id}. Current status is '{order.status}'.")

                    except Order.DoesNotExist:
                        print(f"ERROR: Order with ID {order_id} not found.")
                    except Exception as e:
                        print(f"ERROR: An exception occurred while processing the order: {e}")
                # --- END OF CORRECTED LOGIC ---

            except (IndexError, KeyError):
                pass 

        print("--- WHATSAPP WEBHOOK END ---")
        return HttpResponse("success", status=200)
    
    return HttpResponse("Unsupported method", status=405)