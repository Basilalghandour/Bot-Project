from decimal import Decimal, InvalidOperation
from .models import Customer


def _to_decimal(value, default=Decimal("0.00")):
    """Normalize numeric/str price to Decimal safely."""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def adapt_shopify_order(data, brand=None):
    """Convert Shopify order payload into Order + Customer info (persist + dict)."""
    customer_data = data.get("customer", {}) or {}
    shipping_address = data.get("shipping_address", {}) or {}

    # 🔹 Email always from customer object
    email = customer_data.get("email") or ""

    # 🔹 All other info from shipping address
    first_name = shipping_address.get("first_name") or ""
    last_name = shipping_address.get("last_name") or ""
    phone = shipping_address.get("phone") or ""
    address = shipping_address.get("address1") or ""
    city = shipping_address.get("city") or ""
    state = shipping_address.get("province") or ""
    country = shipping_address.get("country") or ""
    postal_code = shipping_address.get("zip") or None

    # 🔹 Always create a new customer row
    Customer.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        address=address,
        city=city,
        state=state,
        country=country,
        postal_code=postal_code,
    )

    # Adapt order items
    items = []
    for li in data.get("line_items", []) or []:
        qty = li.get("quantity") or li.get("qty") or 1
        price = li.get("price") or li.get("price_per_unit") or li.get("total") or li.get("subtotal") or 0
        items.append({
            "product_name": li.get("name") or li.get("title") or li.get("product_id") or "item",
            "quantity": int(qty),
            "price": str(_to_decimal(price)),
        })

    adapted = {
        "customer": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "country": country,
            "postal_code": postal_code,
        },
        "items": items,
    }

    if "id" in data:
        adapted["external_id"] = str(data.get("id"))

    return adapted


def adapt_woocommerce_order(data, brand=None):
    """Convert WooCommerce order payload into Order + Customer info."""
    shipping = data.get("shipping", {}) or {}
    billing = data.get("billing", {}) or {}

    # Prefer shipping info, fallback to billing
    first_name = shipping.get("first_name") or billing.get("first_name") or ""
    last_name = shipping.get("last_name") or billing.get("last_name") or ""
    email = billing.get("email") or ""
    phone = shipping.get("phone") or billing.get("phone") or ""
    address = shipping.get("address_1") or billing.get("address_1") or ""
    city = shipping.get("city") or billing.get("city") or ""
    state = shipping.get("state") or billing.get("state") or ""
    country = shipping.get("country") or billing.get("country") or ""
    postal_code = shipping.get("postcode") or billing.get("postcode") or None

    # Always create a new customer row
    Customer.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        address=address,
        city=city,
        state=state,
        country=country,
        postal_code=postal_code,
    )

    # Adapt order items with unit price
    items = []
    for li in data.get("line_items", []) or []:
        qty = li.get("quantity") or li.get("qty") or 1
        total = _to_decimal(li.get("total") or 0)
        unit_price = (total / qty) if qty else total
        items.append({
            "product_name": li.get("name") or li.get("title") or "item",
            "quantity": int(qty),
            "price": str(unit_price),
        })

    adapted = {
        "customer": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "country": country,
            "postal_code": postal_code,
        },
        "items": items,
    }

    if "id" in data:
        adapted["external_id"] = str(data.get("id"))

    return adapted


def adapt_incoming_order(data, brand=None):
    """
    Detect payload type and call the correct adapter, returning dict with customer info.
    Always returns: { customer: {...}, items: [...], external_id: str|None }
    """
    if isinstance(data, dict):
        if "line_items" in data and "customer" in data:
            return adapt_shopify_order(data, brand)
        if "line_items" in data and "billing" in data:
            return adapt_woocommerce_order(data, brand)
        if "billing" in data and "line_items" in data:
            return adapt_woocommerce_order(data, brand)
        if "items" in data and isinstance(data.get("items"), list):
            return {
                "customer": data.get("customer", {}),
                "items": data.get("items", []),
                "external_id": str(data.get("external_id")) if data.get("external_id") else None
            }

    return {
        "customer": data.get("customer", {}),
        "items": [],
        "external_id": str(data.get("id")) if data.get("id") else None
    }