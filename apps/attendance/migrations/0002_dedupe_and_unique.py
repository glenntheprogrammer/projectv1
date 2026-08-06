from django.db import migrations, models
from django.db.models import Max


def dedupe_attendance(apps, schema_editor):
    Tblattendance = apps.get_model('attendance', 'Tblattendance')
    grouped = (
        Tblattendance.objects
        .values('student_id', 'attend_date')
        .annotate(keep=Max('attend_id'))
    )
    for item in grouped:
        Tblattendance.objects.filter(
            student_id=item['student_id'],
            attend_date=item['attend_date'],
        ).exclude(attend_id=item['keep']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(dedupe_attendance, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='tblattendance',
            constraint=models.UniqueConstraint(
                fields=['student_id', 'attend_date'],
                name='unique_student_attendance_per_day',
            ),
        ),
    ]
