from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import (
    CategoryForm, CheckoutForm, ContactForm, MedicineForm,
    MedicineSearchForm, PrescriptionUploadForm, ReviewForm,
)
from .models import Category, ContactMessage, Medicine, Order, OrderItem, Prescription, Review


def staff_check(user):
    return user.is_authenticated and (user.is_staff_member if hasattr(user, "is_staff_member") else user.is_staff)


# ---------------------------------------------------------------------------
# Storefront
# ---------------------------------------------------------------------------
def home(request):
    categories = Category.objects.all()[:8]
    featured = Medicine.objects.filter(is_active=True, quantity__gt=0).order_by("-created_at")[:8]
    best_sellers = (
        Medicine.objects.filter(is_active=True)
        .annotate(sold=Count("order_items"))
        .order_by("-sold")[:4]
    )
    return render(request, "store/home.html", {
        "categories": categories,
        "featured": featured,
        "best_sellers": best_sellers,
    })


def medicine_list(request):
    form = MedicineSearchForm(request.GET or None)
    qs = Medicine.objects.filter(is_active=True)

    if form.is_valid():
        q = form.cleaned_data.get("q")
        category = form.cleaned_data.get("category")
        sort = form.cleaned_data.get("sort")
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(company__icontains=q) |
                Q(composition__icontains=q) | Q(uses__icontains=q)
            )
        if category:
            qs = qs.filter(category=category)
        if sort == "price_low":
            qs = qs.order_by("price")
        elif sort == "price_high":
            qs = qs.order_by("-price")
        elif sort == "newest":
            qs = qs.order_by("-created_at")
        else:
            qs = qs.order_by("name")

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "store/medicine_list.html", {
        "form": form,
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "result_count": paginator.count,
    })


def medicine_detail(request, slug):
    medicine = get_object_or_404(Medicine, slug=slug, is_active=True)
    reviews = medicine.reviews.select_related("user")
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
    related = Medicine.objects.filter(category=medicine.category, is_active=True).exclude(pk=medicine.pk)[:4]

    review_form = None
    user_can_review = False
    if request.user.is_authenticated:
        already = reviews.filter(user=request.user).exists()
        user_can_review = not already
        if request.method == "POST" and user_can_review:
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.medicine = medicine
                review.user = request.user
                review.save()
                messages.success(request, "Thanks for your review!")
                return redirect("store:medicine_detail", slug=medicine.slug)
        else:
            review_form = ReviewForm()

    return render(request, "store/medicine_detail.html", {
        "medicine": medicine,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "related": related,
        "review_form": review_form,
        "user_can_review": user_can_review,
    })


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------
def cart_view(request):
    cart = Cart(request)
    return render(request, "store/cart.html", {"cart": cart})


@require_POST
def cart_add(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    cart = Cart(request)
    if medicine.is_out_of_stock:
        messages.error(request, f"{medicine.name} is currently out of stock.")
    else:
        quantity = int(request.POST.get("quantity", 1))
        cart.add(medicine, quantity=quantity)
        messages.success(request, f"Added {medicine.name} to your cart.")
    return redirect(request.POST.get("next") or "store:cart")


@require_POST
def cart_update(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    cart = Cart(request)
    quantity = int(request.POST.get("quantity", 1))
    cart.add(medicine, quantity=quantity, override=True)
    return redirect("store:cart")


@require_POST
def cart_remove(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    Cart(request).remove(medicine)
    messages.info(request, f"Removed {medicine.name} from your cart.")
    return redirect("store:cart")


# ---------------------------------------------------------------------------
# Checkout & Orders
# ---------------------------------------------------------------------------
@login_required
def checkout(request):
    cart = Cart(request)
    if cart.is_empty():
        messages.warning(request, "Your cart is empty.")
        return redirect("store:medicine_list")

    needs_prescription = cart.requires_prescription()
    prescription_form = PrescriptionUploadForm(
        request.POST or None, request.FILES or None
    ) if needs_prescription else None

    initial = {
        "shipping_name": request.user.get_full_name() or request.user.username,
        "shipping_phone": request.user.phone,
        "shipping_address": request.user.address,
        "shipping_city": request.user.city,
        "shipping_pincode": request.user.pincode,
    }

    if request.method == "POST":
        form = CheckoutForm(request.POST, initial=initial)
        prescription_ok = True
        if needs_prescription:
            prescription_ok = prescription_form.is_valid()

        if form.is_valid() and prescription_ok:
            for item in cart:
                if item["quantity"] > item["medicine"].quantity:
                    messages.error(request, f"Only {item['medicine'].quantity} unit(s) of {item['medicine'].name} left in stock.")
                    return redirect("store:cart")

            order = form.save(commit=False)
            order.user = request.user
            order.subtotal = cart.total_price()
            order.delivery_fee = 0 if order.subtotal >= 500 else 40
            order.total_amount = order.subtotal + order.delivery_fee

            if needs_prescription:
                prescription = prescription_form.save(commit=False)
                prescription.user = request.user
                prescription.save()
                order.prescription = prescription

            order.save()

            for item in cart:
                medicine = item["medicine"]
                OrderItem.objects.create(
                    order=order,
                    medicine=medicine,
                    medicine_name=medicine.name,
                    unit_price=medicine.price,
                    quantity=item["quantity"],
                )
                medicine.quantity = max(medicine.quantity - item["quantity"], 0)
                medicine.save(update_fields=["quantity"])

            cart.clear()
            messages.success(request, f"Order {order.order_number} placed successfully!")
            return redirect("store:order_detail", order_number=order.order_number)
    else:
        form = CheckoutForm(initial=initial)

    return render(request, "store/checkout.html", {
        "cart": cart,
        "form": form,
        "prescription_form": prescription_form,
        "needs_prescription": needs_prescription,
    })


@login_required
def order_history(request):
    orders = request.user.orders.all()
    return render(request, "store/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    if request.user.is_staff_member:
        order = get_object_or_404(Order, order_number=order_number)
    else:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "store/order_detail.html", {"order": order})


@login_required
@require_POST
def order_cancel(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.status in (Order.Status.PENDING, Order.Status.PROCESSING):
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
        for item in order.items.all():
            if item.medicine:
                item.medicine.quantity += item.quantity
                item.medicine.save(update_fields=["quantity"])
        messages.success(request, f"Order {order.order_number} cancelled.")
    else:
        messages.error(request, "This order can no longer be cancelled.")
    return redirect("store:order_detail", order_number=order.order_number)


# ---------------------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------------------
def about(request):
    return render(request, "store/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Message sent! Our team will get back to you soon.")
            return redirect("store:contact")
    else:
        form = ContactForm()
    return render(request, "store/contact.html", {"form": form})


# ---------------------------------------------------------------------------
# Staff dashboard
# ---------------------------------------------------------------------------
@user_passes_test(staff_check)
def dashboard_home(request):
    today = timezone.localdate()
    medicines = Medicine.objects.all()
    stats = {
        "total_medicines": medicines.count(),
        "low_stock": medicines.filter(quantity__lte=15, quantity__gt=0).count(),
        "out_of_stock": medicines.filter(quantity__lte=0).count(),
        "expiring_soon": medicines.filter(expiry__lte=today + timezone.timedelta(days=90), expiry__gte=today).count(),
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(status=Order.Status.PENDING).count(),
        "revenue": Order.objects.exclude(status=Order.Status.CANCELLED).aggregate(total=Sum("total_amount"))["total"] or 0,
    }
    recent_orders = Order.objects.select_related("user").all()[:8]
    low_stock_items = medicines.filter(quantity__lte=15).order_by("quantity")[:6]
    expiring_items = medicines.filter(expiry__lte=today + timezone.timedelta(days=90)).order_by("expiry")[:6]
    return render(request, "dashboard/home.html", {
        "stats": stats,
        "recent_orders": recent_orders,
        "low_stock_items": low_stock_items,
        "expiring_items": expiring_items,
    })


@user_passes_test(staff_check)
def dashboard_medicines(request):
    q = request.GET.get("q", "")
    medicines = Medicine.objects.all().order_by("-created_at")
    if q:
        medicines = medicines.filter(Q(name__icontains=q) | Q(company__icontains=q))
    paginator = Paginator(medicines, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/medicine_list.html", {"page_obj": page_obj, "q": q})


@user_passes_test(staff_check)
def dashboard_medicine_form(request, pk=None):
    medicine = get_object_or_404(Medicine, pk=pk) if pk else None
    if request.method == "POST":
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f"Medicine {'updated' if pk else 'added'} successfully.")
            return redirect("store:dashboard_medicines")
    else:
        form = MedicineForm(instance=medicine)
    return render(request, "dashboard/medicine_form.html", {"form": form, "medicine": medicine})


@user_passes_test(staff_check)
@require_POST
def dashboard_medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    medicine.is_active = False
    medicine.save(update_fields=["is_active"])
    messages.success(request, f"{medicine.name} removed from the catalogue.")
    return redirect("store:dashboard_medicines")


@user_passes_test(staff_check)
def dashboard_categories(request):
    categories = Category.objects.annotate(count=Count("medicines"))
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added.")
            return redirect("store:dashboard_categories")
    else:
        form = CategoryForm()
    return render(request, "dashboard/categories.html", {"categories": categories, "form": form})


@user_passes_test(staff_check)
def dashboard_orders(request):
    status = request.GET.get("status", "")
    orders = Order.objects.select_related("user").all()
    if status:
        orders = orders.filter(status=status)
    paginator = Paginator(orders, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/orders.html", {
        "page_obj": page_obj, "status": status, "statuses": Order.Status.choices,
    })


@user_passes_test(staff_check)
@require_POST
def dashboard_order_update_status(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    new_status = request.POST.get("status")
    if new_status in dict(Order.Status.choices):
        order.status = new_status
        order.save(update_fields=["status"])
        messages.success(request, f"Order {order.order_number} marked as {order.get_status_display()}.")
    return redirect("store:dashboard_orders")


@user_passes_test(staff_check)
def dashboard_messages(request):
    contact_messages = ContactMessage.objects.all()
    return render(request, "dashboard/messages.html", {"contact_messages": contact_messages})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
