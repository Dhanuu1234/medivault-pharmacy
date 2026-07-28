from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class MediVaultUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("MediVault profile", {"fields": ("role", "phone", "address", "city", "pincode")}),
    )
    list_display = ("username", "email", "role", "is_staff_member_display", "is_active")
    list_filter = ("role", "is_active")

    def is_staff_member_display(self, obj):
        return obj.is_staff_member
    is_staff_member_display.short_description = "Staff access"
    is_staff_member_display.boolean = True
