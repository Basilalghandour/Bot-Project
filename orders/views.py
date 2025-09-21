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


class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    http_method_names = ['get']
    
    def list(self, request, *args, **kwargs):
        return render(request, 'dashboard.html')
    
    