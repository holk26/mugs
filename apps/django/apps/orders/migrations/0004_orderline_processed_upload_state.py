# Generated manually to bridge master's 0003 to the discount migrations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_orderline_processed_upload_and_more'),
    ]

    operations = [
        # The processed_upload columns were added idempotently in 0003.
        # This migration exists so downstream migrations (0005, 0006) can
        # depend on a stable 0004 node.
    ]
