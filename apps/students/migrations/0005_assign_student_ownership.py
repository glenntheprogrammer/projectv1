from django.contrib.auth import get_user_model
from django.db import migrations


def assign_ownership(apps, schema_editor):
    User = get_user_model()
    Tblstudents = apps.get_model('students', 'Tblstudents')

    first_superuser = User.objects.filter(is_superuser=True).order_by('id').first()

    if first_superuser:
        Tblstudents.objects.filter(user__isnull=True).update(user_id=first_superuser.id)


def reverse_ownership(apps, schema_editor):
    Tblstudents = apps.get_model('students', 'Tblstudents')
    Tblstudents.objects.filter(user__isnull=False).update(user_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0004_tblstudents_user'),
    ]

    operations = [
        migrations.RunPython(assign_ownership, reverse_ownership),
    ]
