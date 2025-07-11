# Generated by Django 5.2.1 on 2025-06-04 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loan',
            name='duration',
            field=models.IntegerField(default=12),
        ),
        migrations.AddField(
            model_name='loan',
            name='purpose',
            field=models.CharField(default='General', max_length=255),
        ),
        migrations.AlterField(
            model_name='loan',
            name='amount',
            field=models.DecimalField(decimal_places=12, max_digits=12),
        ),
    ]
