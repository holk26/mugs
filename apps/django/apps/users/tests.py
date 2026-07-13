import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    assert user.email == 'test@example.com'


@pytest.mark.django_db
def test_ensure_admin_command_creates_admin(monkeypatch):
    monkeypatch.setenv('ADMIN_EMAIL', 'admin@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD', 'secretpass')

    call_command('ensure_admin')

    user = User.objects.get(email='admin@example.com')
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.check_password('secretpass') is True


@pytest.mark.django_db
def test_ensure_admin_command_updates_existing_admin_password(monkeypatch):
    user = User.objects.create_user(
        username='admin@example.com',
        email='admin@example.com',
        password='oldpass',
        is_staff=True,
        is_superuser=True,
    )

    monkeypatch.setenv('ADMIN_EMAIL', 'admin@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD', 'newpass')

    call_command('ensure_admin')

    user.refresh_from_db()
    assert user.check_password('newpass') is True


@pytest.mark.django_db
def test_ensure_admin_command_skips_when_env_not_set(monkeypatch):
    monkeypatch.delenv('ADMIN_EMAIL', raising=False)
    monkeypatch.delenv('ADMIN_PASSWORD', raising=False)

    call_command('ensure_admin')

    assert User.objects.count() == 0
