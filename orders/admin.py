from django.contrib import admin
from .models import Brand, Order, Confirmation, OrderItem

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'website', 'contact_email', 'phone_number', 'created_at')
    search_fields = ('name', 'website', 'contact_email', 'phone_number')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand', 'customer_name', 'customer_phone', 'created_at')
    list_filter = ('brand',)
    search_fields = ('product_name', 'customer_name', 'customer_phone')
    
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id","order", "product_name", "quantity", "price")
    list_filter = ("product_name", "order__created_at")
    search_fields = ("product_name", "order__customer_name", "order__customer_phone")    

@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'status', 'confirmed_at')
    list_filter = ('status',)
    search_fields = ('order__product_name', 'order__customer_name')
