# Generated by Django 4.2.16 on 2024-11-21 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='short_link',
        ),
        migrations.AddField(
            model_name='recipe',
            name='short_link_code',
            field=models.CharField(blank=True, max_length=6, null=True, unique=True),
        ),
    ]
