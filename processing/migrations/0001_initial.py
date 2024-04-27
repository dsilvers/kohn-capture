# Generated by Django 4.2.11 on 2024-04-17 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KohnImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('negative_ocr', models.JSONField(default=list)),
                ('negative_ocr_completed', models.BooleanField(default=False)),
                ('envelope_ocr', models.JSONField(default=list)),
                ('envelope_ocr_completed', models.BooleanField(default=False)),
                ('created_datetime', models.DateTimeField(auto_now_add=True)),
                ('updated_datetime', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]