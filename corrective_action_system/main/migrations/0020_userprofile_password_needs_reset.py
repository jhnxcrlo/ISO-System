# Generated by Django 5.0.6 on 2024-09-19 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_alter_announcement_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='password_needs_reset',
            field=models.BooleanField(default=False),
        ),
    ]
