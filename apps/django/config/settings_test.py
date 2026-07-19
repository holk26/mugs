import os

# Test settings must satisfy the production fail-fast checks in settings.py
# before importing it.
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('STRIPE_WEBHOOK_SECRET', 'test-stripe-webhook-secret')
os.environ.setdefault('PRINTFUL_WEBHOOK_SECRET', 'test-printful-webhook-secret')

from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
