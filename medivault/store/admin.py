from django.contrib import admin

from .models import Category, ContactMessage, Medicine, Order, OrderItem, Prescription, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "category", "price", "quantity", "expiry", "requires_prescription", "is_active")
    list_filter = ("category", "requires_prescription", "is_active", "form")
    search_fields = ("name", "company", "composition")
    prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("medicine", "medicine_name", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "status", "payment_method", "total_amount", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("order_number", "user__username", "shipping_phone")
    inlines = [OrderItemInline]


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "uploaded_at", "verified")
    list_filter = ("verified",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "created_at", "resolved")
    list_filter = ("resolved",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("medicine", "user", "rating", "created_at")
    list_filter = ("rating",)
