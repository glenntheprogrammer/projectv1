from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import migrations


def assign_ownership(apps, schema_editor):
    User = get_user_model()
    Tblcourse = apps.get_model('courses', 'Tblcourse')

    first_superuser = User.objects.filter(is_superuser=True).order_by('id').first()

    if first_superuser:
        Tblcourse.objects.filter(user__isnull=True).update(user_id=first_superuser.id)


def reverse_ownership(apps, schema_editor):
    Tblcourse = apps.get_model('courses', 'Tblcourse')
    Tblcourse.objects.filter(user__isnull=False).update(user_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_tblcourse_user'),
    ]

    operations = [
        migrations.RunPython(assign_ownership, reverse_ownership),
    ]
