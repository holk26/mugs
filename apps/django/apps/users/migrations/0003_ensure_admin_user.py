import os
from django.db import migrations


def ensure_admin_user(apps, schema_editor):
    User = apps.get_model('users', 'User')

    email = os.environ.get('ADMIN_EMAIL') or os.environ.get('USER')
    password = os.environ.get('ADMIN_PASSWORD') or os.environ.get('PASSWORK')

    if not email or not password:
        return

    user, _ = User.objects.update_or_create(
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


def reverse_ensure_admin_user(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_create_admin_user'),
    ]

    operations = [
        migrations.RunPython(ensure_admin_user, reverse_ensure_admin_user),
    ]
