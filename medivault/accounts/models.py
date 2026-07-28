from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        PHARMACIST = "pharmacist", "Pharmacist / Staff"
        ADMIN = "admin", "Administrator"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=12, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_staff_member(self):
        return self.role in (self.Role.PHARMACIST, self.Role.ADMIN) or self.is_superuser

    def __str__(self):
        return self.username
