from rest_framework import serializers
from .models import Brand, Order, Confirmation, OrderItem

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'website', 'contact_email', 'phone_number']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "external_id",
            "brand",
            "customer_name",
            "customer_phone",
            "created_at",
            "forwarded_to_delivery",
            "items"
        ]
        read_only_fields = ["created_at", "forwarded_to_delivery", "brand"]
        
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        external_id = validated_data.pop("external_id", None)

        order = Order.objects.create(external_id=external_id, **validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


class ConfirmationSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    class Meta:
        model = Confirmation
        fields = ['id','order','status','confirmed_at']
