# Generated by Django 5.1.5 on 2025-01-27 22:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0006_remove_profile_website'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_artist',
        ),
    ]
