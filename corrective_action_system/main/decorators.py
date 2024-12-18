# decorators.py

from django.core.exceptions import PermissionDenied

def is_lead_or_internal_auditor(user):
    if user.userprofile.role in ['Lead Auditor', 'Internal Auditor']:
        return True
    raise PermissionDenied  # Return 403 Forbidden for unauthorized users

def is_process_owner(user):
    if user.userprofile.role == 'Process Owner':
        return True
    raise PermissionDenied  # Return 403 Forbidden for unauthorized users
