from .cart import Cart


def cart_summary(request):
    cart = Cart(request)
    return {
        "nav_cart_count": len(cart),
        "site_name": "MediVault",
    }
