from django.conf import settings
from django.db import models


class Tblstudents(models.Model):
    REGULAR = 'regular'
    IRREGULAR = 'irregular'
    ENROLLMENT_TYPES = [
        (REGULAR, 'Regular'),
        (IRREGULAR, 'Irregular'),
    ]

    id = models.AutoField(primary_key=True)
    idno = models.CharField(max_length=50)
    fullname = models.CharField(max_length=255)
    courseid = models.CharField(max_length=50)
    enrollment_type = models.CharField(
        max_length=20,
        choices=ENROLLMENT_TYPES,
        default=REGULAR,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='students',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'tblstudents'

    def __str__(self):
        return self.fullname
