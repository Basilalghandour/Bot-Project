from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from.adapters import adapt_incoming_order
from .models import Brand, Order, Confirmation
from .serializers import BrandSerializer, OrderSerializer, ConfirmationSerializer


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
    
    def create(self, request, *args, **kwargs):
        """
        Accept either native Order payload (items + fields) or raw Shopify/WooCommerce webhook.
        adapt_incoming_order() will normalize to the serializer shape.
        """
        brand_id = self.kwargs.get("brand_pk")
        brand = get_object_or_404(Brand, pk=brand_id) if brand_id else None

        # Normalize incoming payload
        adapted = adapt_incoming_order(request.data, brand=brand)

        serializer = self.get_serializer(data=adapted)
        serializer.is_valid(raise_exception=True)

        # perform_create should accept brand param (we'll call serializer.save with brand)
        if brand:
            order = serializer.save(brand=brand)
        else:
            order = serializer.save()

        # return serialized saved order (refresh to include nested items)
        out_serializer = self.get_serializer(order)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)
        

    """ def perform_create(self, serializer):
        
        This method runs automatically when someone creates an object (POST).
        We override it so we can assign the brand from the URL instead of
        requiring the client to send it in JSON.
        
        brand_id = self.kwargs.get("brand_pk")
        if brand_id:
            brand = get_object_or_404(Brand, pk=brand_id)
            serializer.save(brand=brand)
        else:
            serializer.save() """


class ConfirmationViewSet(viewsets.ModelViewSet):
    queryset = Confirmation.objects.all()
    serializer_class = ConfirmationSerializer
