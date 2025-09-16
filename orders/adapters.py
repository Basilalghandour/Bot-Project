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
    billing_address = data.get("billing_address", {}) or {}

    first_name = customer_data.get("first_name") or billing_address.get("first_name") or ""
    last_name = customer_data.get("last_name") or billing_address.get("last_name") or ""
    email = customer_data.get("email") or billing_address.get("email") or ""
    phone = customer_data.get("phone") or billing_address.get("phone") or ""

    address = billing_address.get("address1") or ""
    city = billing_address.get("city") or ""
    state = billing_address.get("province") or ""
    country = billing_address.get("country") or ""
    postal_code = billing_address.get("zip") or None

    # Save / update customer in DB
    Customer.objects.update_or_create(
        email=email,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "country": country,
            "postal_code": postal_code,
        }
    )

    # Still return dict so your serializers don’t break
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
    billing = data.get("billing", {}) or {}

    first_name = billing.get("first_name") or ""
    last_name = billing.get("last_name") or ""
    email = billing.get("email") or ""
    phone = billing.get("phone") or ""
    address = billing.get("address_1") or ""
    city = billing.get("city") or ""
    state = billing.get("state") or ""
    country = billing.get("country") or ""
    postal_code = billing.get("postcode") or None

    items = []
    for li in data.get("line_items", []) or []:
        qty = li.get("quantity") or li.get("qty") or 1
        # --- CHANGE THIS LINE ---
        # WooCommerce gives "total" (line total) and "price"/"subtotal" can vary.
        # So calculate unit price safely:
        total = _to_decimal(li.get("total") or 0)
        unit_price = (total / qty) if qty else total
        # ------------------------
        items.append({
            "product_name": li.get("name") or li.get("title") or "item",
            "quantity": int(qty),
            "price": str(unit_price),  # save unit price instead of total
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
            # generic fallback
            return {
                "customer": data.get("customer", {}),
                "items": data.get("items", []),
                "external_id": str(data.get("external_id")) if data.get("external_id") else None
            }

    # fallback minimal
    return {
        "customer": data.get("customer", {}),
        "items": [],
        "external_id": str(data.get("id")) if data.get("id") else None
    }
