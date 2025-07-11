# Generated by Django 5.2.2 on 2025-06-09 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_user_options_remove_user_kyc_verified_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='kyc_status',
            field=models.CharField(choices=[('none', 'No KYC Submitted'), ('submitted', 'KYC Submitted - Pending Review'), ('verified', 'KYC Verified'), ('rejected', 'KYC Rejected')], default='none', help_text='Current Know Your Customer (KYC) verification status.', max_length=50),
        ),
        migrations.AlterField(
            model_name='user',
            name='wallet_address',
            field=models.CharField(blank=True, help_text="Ethereum wallet address linked to this user's account.", max_length=42, null=True, unique=True),
        ),
    ]
