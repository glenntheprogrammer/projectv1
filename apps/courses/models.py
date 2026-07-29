from django.db import models


class Tblcourse(models.Model):
    courseid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    section = models.CharField(max_length=100)
    schoolyr = models.CharField(max_length=100)

    class Meta:
        db_table = 'tblcourse'

    def __str__(self):
        return self.name
