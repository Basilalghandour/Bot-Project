from django.db import models

class Brand(models.Model):
    name = models.CharField(max_length=100)
    website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class Order(models.Model):
    external_id = models.CharField(max_length=255, blank=True, null=True, unique=True)  
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="orders")
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    forwarded_to_delivery = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_name} (x{self.quantity})"


class Confirmation(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="confirmation")
    status = models.CharField(
        max_length=10,
        choices=[("pending", "Pending"), ("yes", "Yes"), ("no", "No")],
        default="pending"
    )
    confirmed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.order} - {self.status}"


