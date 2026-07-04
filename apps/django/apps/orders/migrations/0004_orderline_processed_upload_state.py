# Generated manually to extend the existing processed_upload migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_orderline_processed_upload_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderline',
            name='processed_upload',
            field=models.FileField(
                blank=True,
                help_text='AI-cleaned version of the customer drawing ready for Printful',
                null=True,
                upload_to='processed/%Y/%m/%d/',
            ),
        ),
        migrations.AddField(
            model_name='orderline',
            name='processed_upload_generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderline',
            name='processed_upload_error',
            field=models.TextField(blank=True),
        ),
    ]
