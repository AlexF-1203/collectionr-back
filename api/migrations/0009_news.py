# Generated by Django 4.2.20 on 2025-05-25 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_alter_user_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="News",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100)),
                ("content", models.TextField()),
                ("main_image", models.ImageField(upload_to="news/main_image/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
