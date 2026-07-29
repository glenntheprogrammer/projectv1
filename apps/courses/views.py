from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q, Count

from .models import Tblcourse
from apps.students.models import Tblstudents

@login_required(login_url='login')
def course_list_page(request):
    query = request.GET.get('q', '').strip()

    courses_list = Tblcourse.objects.all().order_by('name')

    if query:
        courses_list = courses_list.filter(
            Q(name__icontains=query) |
            Q(courseid__icontains=query) |
            Q(section__icontains=query) |
            Q(schoolyr__icontains=query)
        )

    paginator = Paginator(courses_list, 10)
    page_number = request.GET.get('page', 1)
    courses = paginator.get_page(page_number)

    # courseid on Tblcourse is int; courseid on Tblstudents is varchar,
    # so cast to str for a clean match against the student table.
    course_ids = [str(c.courseid) for c in courses.object_list]
    counts = (
        Tblstudents.objects
        .filter(courseid__in=course_ids)
        .values('courseid')
        .annotate(student_count=Count('id'))
    )
    counts_map = {row['courseid']: row['student_count'] for row in counts}

    for course in courses.object_list:
        course.student_count = counts_map.get(str(course.courseid), 0)

    return render(request, 'courses.html', {
        'courses': courses,
        'query': query,
    })


@login_required(login_url='login')
def course_list_ajax(request):
    courses_list = Tblcourse.objects.all().order_by('name')
    paginator = Paginator(courses_list, 10)
    page_number = request.GET.get('page', 1)
    courses = paginator.get_page(page_number)
    data = list(courses.object_list.values('courseid', 'name', 'section', 'schoolyr'))
    return JsonResponse({
        'data': data,
        'has_next': courses.has_next(),
        'has_prev': courses.has_previous(),
        'page': courses.number,
        'pages': courses.paginator.num_pages,
        'total': courses.paginator.count,
    })


@login_required(login_url='login')
def course_get_ajax(request, pk):
    course = get_object_or_404(Tblcourse, pk=pk)
    return JsonResponse({
        'courseid': course.courseid,
        'name': course.name,
        'section': course.section,
        'schoolyr': course.schoolyr,
    })


@login_required(login_url='login')
@require_POST
def course_save_ajax(request):
    course_id = request.POST.get('courseid', '').strip()

    if course_id:
        course = get_object_or_404(Tblcourse, pk=course_id)
    else:
        course = Tblcourse()

    name = request.POST.get('name', '').strip()
    section = request.POST.get('section', '').strip()
    schoolyr = request.POST.get('schoolyr', '').strip()

    if not name:
        return JsonResponse({'error': 'Course name is required.'}, status=400)
    if not section:
        return JsonResponse({'error': 'Section is required.'}, status=400)
    if not schoolyr:
        return JsonResponse({'error': 'School year is required.'}, status=400)

    course.name = name
    course.section = section
    course.schoolyr = schoolyr

    try:
        course.save()
    except IntegrityError:
        return JsonResponse({'error': 'Could not save course due to a conflict.'}, status=400)

    return JsonResponse({
        'status': 'success',
        'courseid': course.courseid,
        'name': course.name,
        'section': course.section,
        'schoolyr': course.schoolyr,
    })


@login_required(login_url='login')
@require_POST
def course_delete_ajax(request, pk):
    course = get_object_or_404(Tblcourse, pk=pk)
    course.delete()
    return JsonResponse({'status': 'deleted'})
