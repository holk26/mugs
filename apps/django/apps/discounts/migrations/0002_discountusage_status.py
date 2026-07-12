# Generated manually for Block 1: discount usage reservation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='discountusage',
            name='status',
            field=models.CharField(
                choices=[('reserved', 'Reserved'), ('confirmed', 'Confirmed')],
                default='reserved',
                max_length=20,
            ),
        ),
    ]
