from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Create demo accounts (admin, pharmacist, customer) for quick demoing."

    def handle(self, *args, **options):
        demo_accounts = [
            dict(username="admin", email="admin@medivault.example", password="MediVault@123",
                 role=User.Role.ADMIN, is_staff=True, is_superuser=True, first_name="Store"),
            dict(username="pharmacist", email="pharmacist@medivault.example", password="MediVault@123",
                 role=User.Role.PHARMACIST, is_staff=True, is_superuser=False, first_name="Riya"),
            dict(username="customer", email="customer@medivault.example", password="MediVault@123",
                 role=User.Role.CUSTOMER, is_staff=False, is_superuser=False, first_name="Arjun"),
        ]

        for acc in demo_accounts:
            if User.objects.filter(username=acc["username"]).exists():
                self.stdout.write(f"User '{acc['username']}' already exists — skipping.")
                continue
            User.objects.create_user(
                username=acc["username"],
                email=acc["email"],
                password=acc["password"],
                role=acc["role"],
                is_staff=acc["is_staff"],
                is_superuser=acc["is_superuser"],
                first_name=acc["first_name"],
            )
            self.stdout.write(self.style.SUCCESS(f"Created {acc['role']} account: {acc['username']} / {acc['password']}"))
