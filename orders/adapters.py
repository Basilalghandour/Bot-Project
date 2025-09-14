# orders/adapters.py
from decimal import Decimal, InvalidOperation


def _to_decimal(value, default=Decimal("0.00")):
    """Normalize numeric/str price to Decimal safely."""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        # sometimes price comes as "120.00" or 120
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def adapt_shopify_order(data, brand=None):
    """
    Convert a Shopify order payload into your internal OrderSerializer format.
    Returns dict: { customer_name, customer_phone, items: [{product_name, quantity, price}, ...], optional external_id }
    """
    customer = data.get("customer", {}) or {}
    # Shopify sometimes has phone at top-level too
    phone = customer.get("phone") or data.get("phone") or ""
    customer_name = " ".join(
        filter(None, [customer.get("first_name"), customer.get("last_name")])
    ).strip() or data.get("customer_name") or ""

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
        "customer_name": customer_name,
        "customer_phone": phone,
        "items": items,
    }
    # keep external id for debugging/reconciliation
    if "id" in data:
        adapted["external_id"] = str(data.get("id"))
    return adapted


def adapt_woocommerce_order(data, brand=None):
    """
    Convert a WooCommerce order payload into your internal OrderSerializer format.
    WooCommerce uses 'billing' and 'line_items'.
    """
    billing = data.get("billing", {}) or {}
    phone = billing.get("phone") or data.get("customer_phone") or ""
    customer_name = " ".join(
        filter(None, [billing.get("first_name"), billing.get("last_name")])
    ).strip() or data.get("customer_name") or ""

    items = []
    for li in data.get("line_items", []) or []:
        qty = li.get("quantity") or li.get("qty") or 1
        price = li.get("total") or li.get("subtotal") or li.get("price") or 0
        items.append({
            "product_name": li.get("name") or li.get("title") or "item",
            "quantity": int(qty),
            "price": str(_to_decimal(price)),
        })

    adapted = {
        "customer_name": customer_name,
        "customer_phone": phone,
        "items": items,
    }
    if "id" in data:
        adapted["external_id"] = str(data.get("id"))
    return adapted


def adapt_generic_shop_order(data, brand=None):
    """
    Best-effort fallback: try to map common keys.
    """
    # direct expected structure?
    if "customer_name" in data and "items" in data:
        # ensure items have the right keys
        nice_items = []
        for it in data.get("items", []):
            qty = it.get("quantity", it.get("qty", 1))
            price = it.get("price", 0)
            nice_items.append({
                "product_name": it.get("product_name") or it.get("name") or "item",
                "quantity": int(qty),
                "price": str(_to_decimal(price)),
            })
        return {
            "customer_name": data.get("customer_name"),
            "customer_phone": data.get("customer_phone", ""),
            "items": nice_items,
            "external_id": str(data.get("external_id")) if data.get("external_id") else None
        }
    # fallback minimal
    return {
        "customer_name": data.get("customer_name") or data.get("name") or "",
        "customer_phone": data.get("customer_phone") or data.get("phone") or "",
        "items": [],
        "external_id": str(data.get("id")) if data.get("id") else None
    }


def adapt_incoming_order(data, brand=None):
    """
    Detect incoming payload shape and call the right adapter.
    Returns a dict ready for OrderSerializer (without brand, since brand is handled by perform_create).
    """
    # Detect Shopify-ish
    if isinstance(data, dict):
        if "line_items" in data and "customer" in data:
            return adapt_shopify_order(data, brand)
        if "line_items" in data and "billing" in data:
            return adapt_woocommerce_order(data, brand)
        if "billing" in data and "line_items" in data:
            return adapt_woocommerce_order(data, brand)
        # some shops use 'items' or 'order_items'
        if "items" in data and isinstance(data.get("items"), list):
            # check first item keys for 'product_name' or 'name'
            first = (data.get("items") or [None])[0]
            if first and ("name" in first or "product_name" in first):
                return adapt_generic_shop_order(data, brand)

    # otherwise fallback
    return adapt_generic_shop_order(data, brand)
