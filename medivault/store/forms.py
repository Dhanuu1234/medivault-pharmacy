from django import forms

from .models import Category, ContactMessage, Medicine, Order, Prescription, Review


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "shipping_name", "shipping_phone", "shipping_address",
            "shipping_city", "shipping_pincode", "payment_method",
        ]
        widgets = {
            "shipping_address": forms.Textarea(attrs={"rows": 3}),
        }


class PrescriptionUploadForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["image", "note"]
        widgets = {"note": forms.TextInput(attrs={"placeholder": "Prescribing doctor / notes (optional)"})}


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} star{'s' if i != 1 else ''}") for i in range(1, 6)]),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Share your experience (optional)"}),
        }


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = [
            "name", "company", "category", "form", "composition", "description",
            "uses", "dosage", "side_effects", "precautions", "price", "quantity",
            "expiry", "batch_no", "requires_prescription", "image_emoji", "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "uses": forms.Textarea(attrs={"rows": 3, "placeholder": "One condition per line"}),
            "side_effects": forms.Textarea(attrs={"rows": 3, "placeholder": "One side effect per line"}),
            "precautions": forms.Textarea(attrs={"rows": 3, "placeholder": "One precaution per line"}),
            "expiry": forms.DateInput(attrs={"type": "date"}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "icon", "description"]


class MedicineSearchForm(forms.Form):
    q = forms.CharField(required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("name", "Name (A-Z)"),
            ("price_low", "Price: Low to High"),
            ("price_high", "Price: High to Low"),
            ("newest", "Newest First"),
        ],
    )
