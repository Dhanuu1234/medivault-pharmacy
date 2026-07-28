from decimal import Decimal

from .models import Medicine

CART_SESSION_KEY = "medivault_cart"


class Cart:
    """A simple session-backed shopping cart. Keys are medicine IDs (as str), values are quantities."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, medicine, quantity=1, override=False):
        key = str(medicine.id)
        if key not in self.cart:
            self.cart[key] = 0
        if override:
            self.cart[key] = quantity
        else:
            self.cart[key] += quantity
        max_qty = max(medicine.quantity, 0)
        if self.cart[key] > max_qty:
            self.cart[key] = max_qty
        if self.cart[key] <= 0:
            self.remove(medicine)
        else:
            self.save()

    def remove(self, medicine):
        key = str(medicine.id)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.save()

    def __iter__(self):
        ids = self.cart.keys()
        medicines = Medicine.objects.filter(id__in=ids)
        medicine_map = {str(m.id): m for m in medicines}
        for key, qty in self.cart.items():
            medicine = medicine_map.get(key)
            if not medicine:
                continue
            yield {
                "medicine": medicine,
                "quantity": qty,
                "line_total": medicine.price * qty,
            }

    def __len__(self):
        return sum(self.cart.values())

    def total_price(self):
        total = Decimal("0.00")
        for item in self:
            total += item["line_total"]
        return total

    def is_empty(self):
        return len(self.cart) == 0

    def requires_prescription(self):
        return any(item["medicine"].requires_prescription for item in self)
