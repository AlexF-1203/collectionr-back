# Generated by Django 4.2.9 on 2025-02-24 15:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_remove_collection_is_foil_remove_collection_notes_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="set",
            name="code",
            field=models.CharField(max_length=20),
        ),
        migrations.AlterUniqueTogether(
            name="set",
            unique_together={("user", "code")},
        ),
    ]
