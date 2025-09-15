from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from.adapters import adapt_incoming_order
from .models import Brand, Order, Confirmation
from .serializers import BrandSerializer, OrderSerializer, ConfirmationSerializer
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def webhook(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Invalid method"}, status=405)

        raw_body = request.body.decode("utf-8")
        print("Webhook raw body:", raw_body)

        # Try to parse JSON first
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            # If not JSON, fallback to POST form data
            payload = request.POST.dict()

        print("Parsed payload:", payload)

        # TODO: Here you can later map `payload` into your Order model

        return JsonResponse({"status": "ok"})

    except Exception as e:
        print("Webhook error:", str(e))
        return JsonResponse({"error": str(e)}, status=400)




class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        """
        If 'brand_pk' is in kwargs (nested route), filter by that brand.
        Otherwise, return all orders.
        """
        brand_id = self.kwargs.get("brand_pk")
        if brand_id:
            get_object_or_404(Brand, pk=brand_id)
            return Order.objects.filter(brand_id=brand_id)  # <-- change here
        return Order.objects.all()
    
    @csrf_exempt    
    def create(self, request, *args, **kwargs):
        """
        Accept either native Order payload (items + fields) or raw Shopify/WooCommerce webhook.
        adapt_incoming_order() will normalize to the serializer shape.
        """
        brand_id = self.kwargs.get("brand_pk")
        brand = None

        if brand_id:
            # Nested route: /brands/<brand_id>/orders/
            brand = get_object_or_404(Brand, pk=brand_id)
        else:
            # Generic webhook route: /webhook/
            # Try to detect the brand from the payload (adjust this to match your payload)
            # Example: WooCommerce may send 'store_domain' or meta info
            domain = request.data.get("store_domain") or request.data.get("meta_data", [{}])[0].get("value")
            if domain:
                brand = Brand.objects.filter(website__icontains=domain).first()

        # Normalize incoming payload
        adapted = adapt_incoming_order(request.data, brand=brand)

        serializer = self.get_serializer(data=adapted)
        serializer.is_valid(raise_exception=True)

        # Save with brand if found
        if brand:
            order = serializer.save(brand=brand)
        else:
            order = serializer.save()

        # Return serialized saved order (refresh to include nested items)
        out_serializer = self.get_serializer(order)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)
        



class ConfirmationViewSet(viewsets.ModelViewSet):
    queryset = Confirmation.objects.all()
    serializer_class = ConfirmationSerializer
