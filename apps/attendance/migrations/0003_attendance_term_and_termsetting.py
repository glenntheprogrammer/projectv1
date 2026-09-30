from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_terms_to_existing_records(apps, schema_editor):
    """Place records that predate the term column into the right term.

    The column arrives defaulting to 'prelim', which already covers the
    Aug-Nov stretch, so only the other months need reassigning. These month
    boundaries are a one-off guess for historic rows; everything saved from
    now on is stamped with whichever term is active at the time.
    """
    Tblattendance = apps.get_model('attendance', 'Tblattendance')

    Tblattendance.objects.filter(attend_date__month=12).update(term='midterm')
    Tblattendance.objects.filter(attend_date__month=1).update(term='midterm')

    for month in range(2, 8):
        Tblattendance.objects.filter(attend_date__month=month).update(term='endterm')


def seed_default_active_term(apps, schema_editor):
    Tbltermsetting = apps.get_model('attendance', 'Tbltermsetting')
    user_model = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    for user in user_model.objects.all():
        Tbltermsetting.objects.get_or_create(
            user=user,
            defaults={'active_term': 'prelim'},
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('attendance', '0002_dedupe_and_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='tblattendance',
            name='term',
            field=models.CharField(choices=[('prelim', 'Prelim'), ('midterm', 'Midterm'), ('endterm', 'End term')], default='prelim', max_length=20),
        ),
        migrations.CreateModel(
            name='Tbltermsetting',
            fields=[
                ('setting_id', models.AutoField(primary_key=True, serialize=False)),
                ('active_term', models.CharField(choices=[('prelim', 'Prelim'), ('midterm', 'Midterm'), ('endterm', 'End term')], default='prelim', max_length=20)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='term_setting', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tbltermsetting',
            },
        ),
        migrations.RunPython(assign_terms_to_existing_records, migrations.RunPython.noop),
        migrations.RunPython(seed_default_active_term, migrations.RunPython.noop),
    ]
