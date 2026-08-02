from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q, Count

from apps.attendance.models import Tblattendance
from apps.courses.models import Tblcourse
from .models import Tblstudents


def _get_course_display(course_id):
    if not course_id:
        return ''

    course_ids = [cid.strip() for cid in str(course_id).split(',') if cid.strip()]
    if not course_ids:
        return course_id

    courses = Tblcourse.objects.filter(courseid__in=course_ids)
    course_map = {
        str(course.courseid): f"{course.name} - {course.section} ({course.schoolyr})"
        for course in courses
    }

    return ', '.join(course_map.get(cid, cid) for cid in course_ids)


@login_required(login_url='login')
def student_list_page(request, course_id=None):
    query = request.GET.get('q', '').strip()

    students_list = Tblstudents.objects.select_related().all().order_by('fullname')

    if course_id:
        students_list = students_list.filter(courseid=course_id)

    if query:
        students_list = students_list.filter(
            Q(fullname__icontains=query) |
            Q(idno__icontains=query) |
            Q(courseid__icontains=query)
        )

    paginator = Paginator(students_list, 10)
    page_number = request.GET.get('page', 1)
    students = paginator.get_page(page_number)

    courses = Tblcourse.objects.filter(status='active').order_by('name')

    selected_course_name = None
    if course_id:
        selected_course = Tblcourse.objects.filter(courseid=course_id).first()
        if selected_course:
            selected_course_name = selected_course.name

    student_rows = []
    for student in students:
        attendance_counts = Tblattendance.objects.filter(student_id=student).values('status').annotate(count=Count('status'))
        attendance_map = {item['status']: item['count'] for item in attendance_counts}

        student_rows.append({
            'id': student.id,
            'idno': student.idno,
            'fullname': student.fullname,
            'courseid': student.courseid,
            'course_display': _get_course_display(student.courseid),
            'attendance_counts': {
                'present_count': attendance_map.get('1', 0),
                'late_count': attendance_map.get('2', 0),
                'absent_count': attendance_map.get('3', 0),
                'excused_count': attendance_map.get('4', 0),
            },
        })

    return render(request, 'students.html', {
        'students': student_rows,
        'students_page': students,  # pass the raw Page object for pagination controls
        'query': query,
        'courses': courses,
        'selected_course_id': course_id,
        'selected_course_name': selected_course_name,
    })


@login_required(login_url='login')
def student_list_ajax(request):
    query = request.GET.get('q', '').strip()
    course_id = request.GET.get('course_id', '').strip()

    students_list = Tblstudents.objects.all().order_by('fullname')

    if course_id:
        students_list = students_list.filter(courseid=course_id)

    if query:
        students_list = students_list.filter(
            Q(fullname__icontains=query) |
            Q(idno__icontains=query) |
            Q(courseid__icontains=query)
        )

    paginator = Paginator(students_list, 50)
    page_number = request.GET.get('page', 1)
    students = paginator.get_page(page_number)
    data = list(students.object_list.values('id', 'idno', 'fullname', 'courseid'))
    return JsonResponse({
        'data': data,
        'has_next': students.has_next(),
        'has_prev': students.has_previous(),
        'page': students.number,
        'pages': students.paginator.num_pages,
        'total': students.paginator.count,
    })


@login_required(login_url='login')
def student_get_ajax(request, pk):
    student = get_object_or_404(Tblstudents, pk=pk)
    return JsonResponse({
        'id': student.id,
        'idno': student.idno,
        'fullname': student.fullname,
        'courseid': student.courseid,
    })


@login_required(login_url='login')
@require_POST
def student_save_ajax(request):
    student_id = request.POST.get('id')

    if student_id:
        student = get_object_or_404(Tblstudents, pk=student_id)
    else:
        student = Tblstudents()

    idno = request.POST.get('idno', '').strip()
    fullname = request.POST.get('fullname', '').strip()
    course_ids = request.POST.getlist('courseid')
    course_ids = [cid.strip() for cid in course_ids if cid.strip()]

    if not idno:
        return JsonResponse({'error': 'Student ID number is required.'}, status=400)
    if not fullname:
        return JsonResponse({'error': 'Full name is required.'}, status=400)
    if not course_ids:
        return JsonResponse({'error': 'At least one course must be selected.'}, status=400)

    existing_course_ids = set(str(cid) for cid in Tblcourse.objects.filter(courseid__in=course_ids).values_list('courseid', flat=True))
    invalid_course_ids = [cid for cid in course_ids if cid not in existing_course_ids]
    if invalid_course_ids:
        return JsonResponse({'error': 'One or more selected courses do not exist.'}, status=400)

    if student.pk and len(course_ids) == 1:
        duplicate_qs = Tblstudents.objects.filter(
            idno=idno,
            fullname=fullname,
            courseid=course_ids[0],
        ).exclude(pk=student.pk)
        if duplicate_qs.exists():
            return JsonResponse({'error': 'A student with the same ID number, name, and course already exists.'}, status=400)

        student.idno = idno
        student.fullname = fullname
        student.courseid = course_ids[0]

        try:
            student.save()
        except IntegrityError:
            return JsonResponse({'error': 'Could not save student due to a conflict.'}, status=400)

        return JsonResponse({
            'status': 'success',
            'id': student.id,
            'idno': student.idno,
            'fullname': student.fullname,
            'courseid': student.courseid,
        })

    created_students = []
    for course_id in course_ids:
        duplicate_qs = Tblstudents.objects.filter(
            idno=idno,
            fullname=fullname,
            courseid=course_id,
        )
        if student.pk:
            duplicate_qs = duplicate_qs.exclude(pk=student.pk)

        if duplicate_qs.exists():
            continue

        student_record = Tblstudents(
            idno=idno,
            fullname=fullname,
            courseid=course_id,
        )
        try:
            student_record.save()
        except IntegrityError:
            return JsonResponse({'error': 'Could not save student due to a conflict.'}, status=400)

        created_students.append(student_record)

    if student.pk:
        student.delete()

    if not created_students:
        return JsonResponse({'error': 'Student already exists for all selected courses.'}, status=400)

    first_student = created_students[0]
    return JsonResponse({
        'status': 'success',
        'id': first_student.id,
        'idno': first_student.idno,
        'fullname': first_student.fullname,
        'courseid': first_student.courseid,
        'created_count': len(created_students),
    })


@login_required(login_url='login')
@require_POST
def student_delete_ajax(request, pk):
    student = get_object_or_404(Tblstudents, pk=pk)
    student.delete()
    return JsonResponse({'status': 'deleted'})