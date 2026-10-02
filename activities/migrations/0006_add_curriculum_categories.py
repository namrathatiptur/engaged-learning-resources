from django.db import migrations

CATEGORIES = [
    "Group Activity",
    "Individual Activity",
    "Whole Class Activity",
    "Creative Visual Activity",
    "Creative Performance Activity",
    "Class Presentation Component",
    "Outside of Classroom Activity",
    "Civic Engagement",
    "Policy",
    "Business and Economics",
]


def add_categories(apps, schema_editor):
    Category = apps.get_model("activities", "Category")
    for name in CATEGORIES:
        Category.objects.get_or_create(name=name)


def remove_categories(apps, schema_editor):
    Category = apps.get_model("activities", "Category")
    Category.objects.filter(name__in=CATEGORIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0005_material_preview_pdf"),
    ]

    operations = [
        migrations.RunPython(add_categories, remove_categories),
    ]
