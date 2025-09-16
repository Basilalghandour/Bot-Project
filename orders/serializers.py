from rest_framework import serializers
from .models import *

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'website', 'contact_email', 'phone_number']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "quantity", "price"]

class CustomerSerializer(serializers.ModelSerializer):
    orders = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "orders",
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = CustomerSerializer(read_only=True)  # 🔹 Make read-only

    class Meta:
        model = Order
        fields = [
            "id",
            "external_id",
            "brand",
            "customer",
            "created_at",
            "forwarded_to_delivery",
            "items"
        ]
        read_only_fields = ["created_at", "forwarded_to_delivery", "brand", "customer"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        external_id = validated_data.pop("external_id", None)
        # 🔹 Get the customer instance from context
        customer = self.context.get('customer')

        order = Order.objects.create(external_id=external_id, customer=customer, **validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order



class ConfirmationSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    class Meta:
        model = Confirmation
        fields = ['id','order','status','confirmed_at']
