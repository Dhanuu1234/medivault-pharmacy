from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=10, default="💊", help_text="Emoji shown on the category chip")
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Medicine(models.Model):
    class Form(models.TextChoices):
        TABLET = "tablet", "Tablet"
        CAPSULE = "capsule", "Capsule"
        SYRUP = "syrup", "Syrup"
        INJECTION = "injection", "Injection"
        OINTMENT = "ointment", "Ointment / Cream"
        DROPS = "drops", "Drops"
        POWDER = "powder", "Powder / Sachet"
        DEVICE = "device", "Medical Device"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    company = models.CharField(max_length=100, help_text="Manufacturer")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="medicines")
    form = models.CharField(max_length=20, choices=Form.choices, default=Form.TABLET)
    composition = models.CharField(max_length=255, blank=True, help_text="Active salt / composition")
    description = models.TextField(blank=True, help_text="What this medicine is and how it helps")
    uses = models.TextField(blank=True, help_text="Conditions this medicine is used for, one per line")
    dosage = models.CharField(max_length=255, blank=True, help_text="Typical adult dosage guidance")
    side_effects = models.TextField(blank=True, help_text="Common side effects, one per line")
    precautions = models.TextField(blank=True, help_text="Warnings / precautions, one per line")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0, help_text="Units currently in stock")
    expiry = models.DateField()
    batch_no = models.CharField(max_length=40, blank=True)
    requires_prescription = models.BooleanField(default=False)
    image_emoji = models.CharField(max_length=10, default="💊")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while Medicine.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:medicine_detail", args=[self.slug])

    @property
    def is_low_stock(self):
        from django.conf import settings as dj_settings
        return self.quantity <= getattr(dj_settings, "LOW_STOCK_THRESHOLD", 15)

    @property
    def is_out_of_stock(self):
        return self.quantity <= 0

    @property
    def is_expiring_soon(self):
        from django.conf import settings as dj_settings
        days = getattr(dj_settings, "EXPIRY_WARNING_DAYS", 90)
        return self.expiry <= timezone.localdate() + timezone.timedelta(days=days)

    @property
    def is_expired(self):
        return self.expiry < timezone.localdate()

    def uses_list(self):
        return [u.strip() for u in self.uses.splitlines() if u.strip()]

    def side_effects_list(self):
        return [s.strip() for s in self.side_effects.splitlines() if s.strip()]

    def precautions_list(self):
        return [p.strip() for p in self.precautions.splitlines() if p.strip()]

    def __str__(self):
        return f"{self.name} ({self.company})"


class Prescription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prescriptions")
    image = models.ImageField(upload_to="prescriptions/%Y/%m/")
    note = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Prescription #{self.pk} - {self.user}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Confirmation"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class Payment(models.TextChoices):
        COD = "cod", "Cash on Delivery"
        ONLINE = "online", "Online Payment"

    order_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(max_length=10, choices=Payment.choices, default=Payment.COD)
    shipping_name = models.CharField(max_length=150)
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_pincode = models.CharField(max_length=12)
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"MV{timezone.now().strftime('%y%m%d')}{str(timezone.now().microsecond)[:4]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, related_name="order_items")
    medicine_name = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.medicine_name} x{self.quantity}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} - {self.name}"


class Review(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("medicine", "user")

    def __str__(self):
        return f"{self.rating}★ - {self.medicine.name}"
