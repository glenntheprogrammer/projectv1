from .terms import get_active_term, term_label


def active_term(request):
    """Expose the active term everywhere so the sidebar can always show it."""
    if not request.user.is_authenticated:
        return {}

    active = get_active_term(request.user)

    return {
        'active_term': active,
        'active_term_label': term_label(active),
    }