from django.db.models import Count

from apps.scoping import scoped_attendance
from .models import DEFAULT_TERM, TERM_CHOICES, TERM_LABELS, Tbltermsetting

STATUS_KEYS = {
    '1': 'present_count',
    '2': 'late_count',
    '3': 'absent_count',
    '4': 'excused_count',
}


def empty_counts():
    return {
        'present_count': 0,
        'late_count': 0,
        'absent_count': 0,
        'excused_count': 0,
    }


def status_counts(queryset):
    """Count a queryset of Tblattendance rows by status code."""
    counts = empty_counts()
    annotated = queryset.values('status').annotate(count=Count('status'))

    for item in annotated:
        key = STATUS_KEYS.get(item['status'])
        if key:
            counts[key] = item['count']

    return counts


def term_label(term):
    return TERM_LABELS.get(term, term)


def get_active_term(user):
    """The term the user is currently recording attendance for.

    Defaults to Prelim so a brand new account behaves sensibly without
    anyone having to visit Settings first.
    """
    active = Tbltermsetting.objects.filter(user=user).values_list('active_term', flat=True).first()
    return active if active in TERM_LABELS else DEFAULT_TERM


def set_active_term(user, term):
    Tbltermsetting.objects.update_or_create(user=user, defaults={'active_term': term})
    return term


def view_term(request):
    """The term a page should report on.

    Defaults to the user's active term. An explicit ?term= lets someone look
    back at a finished term without changing what new records are stamped with.
    """
    requested = request.GET.get('term', '').strip()
    if requested in TERM_LABELS:
        return requested

    return get_active_term(request.user)


def filter_by_term(queryset, term):
    return queryset.filter(term=term)


def term_breakdown(user):
    """P/L/A/E totals for every term, for the Settings page."""
    rows = []

    for slug, label in TERM_CHOICES:
        counts = status_counts(scoped_attendance(user).filter(term=slug))
        rows.append({
            'slug': slug,
            'label': label,
            'counts': counts,
            'total': sum(counts.values()),
        })

    return rows


def term_context(request):
    """Template context shared by every page that reports on a term."""
    active = get_active_term(request.user)
    current = view_term(request)

    return {
        'active_term': active,
        'active_term_label': term_label(active),
        'view_term': current,
        'view_term_label': term_label(current),
        'is_active_term_view': current == active,
        'term_choices': TERM_CHOICES,
    }
