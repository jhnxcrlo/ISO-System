# Generated by Django 5.0.6 on 2024-09-07 14:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rfa',
            name='originator',
        ),
        migrations.DeleteModel(
            name='Comment',
        ),
        migrations.DeleteModel(
            name='RFA',
        ),
    ]
