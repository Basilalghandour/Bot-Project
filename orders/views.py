from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from.adapters import adapt_incoming_order
from .models import *
from .serializers import *
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        brand_id = self.kwargs.get("brand_pk")
        if brand_id:
            get_object_or_404(Brand, pk=brand_id)
            return Order.objects.filter(brand_id=brand_id)
        return Order.objects.all()

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        print("Incoming payload:", json.dumps(request.data, indent=2))
        brand_id = self.kwargs.get("brand_pk")
        brand = None

        if brand_id:
            brand = get_object_or_404(Brand, pk=brand_id)
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
