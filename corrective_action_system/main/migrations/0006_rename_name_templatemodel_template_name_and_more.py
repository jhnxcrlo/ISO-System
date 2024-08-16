# Generated by Django 5.0.6 on 2024-08-15 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_templatemodel'),
    ]

    operations = [
        migrations.RenameField(
            model_name='templatemodel',
            old_name='name',
            new_name='template_name',
        ),
        migrations.RemoveField(
            model_name='templatemodel',
            name='uploaded_at',
        ),
        migrations.AddField(
            model_name='templatemodel',
            name='description',
            field=models.TextField(default='No description provided'),
        ),
        migrations.AddField(
            model_name='templatemodel',
            name='file',
            field=models.FileField(default='Default Name', upload_to='templates/'),
            preserve_default=False,
        ),
    ]
