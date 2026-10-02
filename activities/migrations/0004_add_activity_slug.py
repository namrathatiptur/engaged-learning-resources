# Generated manually for slug support (raw SQL to avoid PostgreSQL index conflicts)

from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    Activity = apps.get_model("activities", "Activity")
    for activity in Activity.objects.all():
        base = slugify(activity.title) or "activity"
        slug = base
        n = 1
        while Activity.objects.filter(slug=slug).exclude(pk=activity.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        activity.slug = slug
        activity.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0003_add_performance_indexes"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE activities_activity ADD COLUMN slug VARCHAR(255) NOT NULL DEFAULT ''",
            reverse_sql="ALTER TABLE activities_activity DROP COLUMN slug",
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="activity",
                    name="slug",
                    field=models.SlugField(blank=True, max_length=255, unique=False),
                ),
            ],
            database_operations=[],
        ),
        migrations.RunPython(populate_slugs, noop),
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS activities_activity_slug_uniq ON activities_activity (slug)",
            reverse_sql="DROP INDEX IF EXISTS activities_activity_slug_uniq",
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="activity",
                    name="slug",
                    field=models.SlugField(max_length=255, unique=True),
                ),
            ],
            database_operations=[],
        ),
    ]
