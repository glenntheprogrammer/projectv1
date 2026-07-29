from django.db import models

from apps.students.models import Tblstudents


class Tblattendance(models.Model):
    attend_id = models.AutoField(primary_key=True)
    attend_date = models.DateField()
    student_id = models.ForeignKey(Tblstudents, on_delete=models.CASCADE, db_column='student_id', to_field='id')
    status = models.CharField(max_length=50)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tblattendance'

    def __str__(self):
        return f"{self.student_id} - {self.status}"
