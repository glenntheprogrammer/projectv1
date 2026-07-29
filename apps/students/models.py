from django.db import models


class Tblstudents(models.Model):
    id = models.AutoField(primary_key=True)
    idno = models.CharField(max_length=50)
    fullname = models.CharField(max_length=255)
    courseid = models.CharField(max_length=50)

    class Meta:
        db_table = 'tblstudents'

    def __str__(self):
        return self.fullname
