from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update the admin user from ADMIN_EMAIL and ADMIN_PASSWORD env vars.'

    def handle(self, *args, **options):
        import os

        email = os.environ.get('ADMIN_EMAIL', '').strip()
        password = os.environ.get('ADMIN_PASSWORD', '').strip()

        if not email or not password:
            self.stdout.write(self.style.WARNING('ADMIN_EMAIL and ADMIN_PASSWORD not set; skipping admin creation.'))
            return

        user, created = User.objects.update_or_create(
            email=email,
            defaults={
                'username': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        user.set_password(password)
        user.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} admin user {email}.'))
