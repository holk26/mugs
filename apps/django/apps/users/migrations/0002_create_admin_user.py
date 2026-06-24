import os
from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_admin_user(apps, schema_editor):
    User = apps.get_model('users', 'User')

    email = os.environ.get('ADMIN_EMAIL') or os.environ.get('USER')
    password = os.environ.get('ADMIN_PASSWORD') or os.environ.get('PASSWORK')

    if not email or not password:
        return

    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
    else:
        user = User(email=email, username=email)

    user.password = make_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()


def reverse_create_admin_user(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_admin_user, reverse_create_admin_user),
    ]
