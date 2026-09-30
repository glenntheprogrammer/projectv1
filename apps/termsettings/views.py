from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.attendance.models import TERM_LABELS
from apps.attendance.terms import get_active_term, set_active_term, term_breakdown, term_label


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def term_settings_view(request):
    active = get_active_term(request.user)
    error = ''

    if request.method == 'POST':
        requested = request.POST.get('active_term', '').strip()

        if requested not in TERM_LABELS:
            error = 'Please choose a valid term.'
        else:
            set_active_term(request.user, requested)
            return redirect(f"{reverse('termsettings:term_settings')}?saved=1")

    return render(request, 'term_settings.html', {
        'term_rows': term_breakdown(request.user),
        'active_term': active,
        'active_term_label': term_label(active),
        'error': error,
        'saved': request.GET.get('saved') == '1',
    })
