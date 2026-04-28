def cart_count(request):
    cart = request.session.get("cart", {})

    count = sum(
        item.get("quantity", 0) if isinstance(item, dict) else 0
        for item in cart.values()
    )

    return {"cart_count": count}


def cart_data(request):
    cart = request.session.get("cart", {})

    cart_count = sum(
        item.get("quantity", 0) if isinstance(item, dict) else 0
        for item in cart.values()
    )

    return {
        "cart_count": cart_count,
        "cart": cart
    }