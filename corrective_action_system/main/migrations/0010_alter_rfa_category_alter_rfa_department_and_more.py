# Generated by Django 5.0.6 on 2024-09-02 17:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_rfa'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='rfa',
            name='category',
            field=models.CharField(choices=[('Major', 'Major'), ('Minor', 'Minor')], default='Minor', max_length=10),
        ),
        migrations.AlterField(
            model_name='rfa',
            name='department',
            field=models.CharField(default='General', max_length=100),
        ),
        migrations.AlterField(
            model_name='rfa',
            name='description',
            field=models.TextField(default='No description provided'),
        ),
        migrations.AlterField(
            model_name='rfa',
            name='immediate_action',
            field=models.TextField(default='No immediate action provided'),
        ),
        migrations.AlterField(
            model_name='rfa',
            name='iso_clause_reference',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='rfa',
            name='non_conformity_type',
            field=models.CharField(choices=[('IQA', 'IQA-Related'), ('Supplier', 'Supplier-Related'), ('3rd_Party', '3rd Party Audit Related'), ('Customer', 'Customer Satisfaction Related'), ('Process', 'Process/Procedural-related'), ('HRD', 'HRD-Related'), ('KPI', 'Relates to KPI/Quality Objective Review'), ('Other', 'Others')], default='Other', max_length=20),
        ),
        migrations.AlterField(
            model_name='rfa',
            name='originator',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='rfa',
            name='reference_number',
            field=models.CharField(default='DEFAULT_REF', max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='rfa',
            name='responsible_officer',
            field=models.CharField(blank=True, default='N/A', max_length=100),
        ),
    ]
