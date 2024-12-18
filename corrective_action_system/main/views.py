# views.py

from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models import Prefetch
from django.template.loader import render_to_string, get_template
from django.urls import resolve, reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse, FileResponse, Http404, HttpResponseServerError, HttpResponseForbidden, \
    JsonResponse
from django.templatetags.static import static
from django.contrib import messages
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_protect
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from xhtml2pdf import pisa
import logging

from notifications.signals import notify
from notifications.models import Notification

from .decorators import is_process_owner
from .models import (
    LoginEvent, UserProfile, ImmediateAction, RootCauseAnalysis,
    CorrectiveActionPlan, FollowUpAction, ActionVerification,
    CorrectiveActionPlanReview, CloseOut, Comment, NonConformity,
    TemplateModel, Guideline, Announcement, AuditDetails, GoodPoints, AuditFinding, Evaluation
)

from .forms import (
    UserCreationForm, UserUpdateForm, RootCauseAnalysisForm,
    ImmediateActionForm, CorrectiveActionPlanForm, FollowUpActionForm,
    CorrectiveActionPlanReviewForm, CloseOutForm, ActionVerificationForm,
    GuidelineForm, AnnouncementForm, CustomPasswordChangeForm, AuditDetailsForm, GoodPointsForm, AuditFindingForm,
    EvaluationForm
)

s = URLSafeTimedSerializer('your-secret-key')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)

            LoginEvent.objects.create(user=user)
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            request.session['user_role'] = user_profile.role

            # Redirect based on user role
            if user_profile.role == 'Internal Auditor':
                return redirect('internal_auditor_dashboard')
            elif user_profile.role == 'Process Owner':
                return redirect('process_owner_dashboard')
            elif user_profile.role == 'Lead Auditor':
                return redirect('lead_auditor_dashboard')
            else:
                return redirect('lead_auditor_dashboard')
        else:
            return render(request, 'main/login.html', {'error': 'Invalid username or password'})
    return render(request, 'main/login.html')


@login_required
def lead_auditor_dashboard_view(request):
    total_non_conformities_count = NonConformity.objects.count()
    total_ofi_count = NonConformity.objects.filter(rfa_intent='improvement').count()
    major_nc_count = NonConformity.objects.filter(category='major').count()
    minor_nc_count = NonConformity.objects.filter(category='minor').count()
    ofi_count = NonConformity.objects.filter(rfa_intent='improvement').count()
    good_points_count = AuditFinding.objects.filter(finding_type='Good Points').count()
    internal_auditors_count = UserProfile.objects.filter(role='Internal Auditor').count()
    process_owners_count = UserProfile.objects.filter(role='Process Owner').count()

    total_members = internal_auditors_count + process_owners_count
    audit_details = AuditDetails.objects.last()

    iso_clauses = {
        '4': "Context of the Organization",
        '5': "Leadership",
        '6': "Planning",
        '7': "Support",
        '8': "Operation",
        '9': "Performance Evaluation",
        '10': "Improvement",
    }

    non_conformities = NonConformity.objects.all()
    # Fetch Internal Auditors and Process Owners in one query
    members = UserProfile.objects.filter(role__in=['Internal Auditor', 'Process Owner']).select_related('user')

    context = {
        "total_non_conformities_count": total_non_conformities_count,
        "total_ofi_count": total_ofi_count,
        "major_nc_count": major_nc_count,
        "minor_nc_count": minor_nc_count,
        "ofi_count": ofi_count,
        "good_points_count": good_points_count,
        "internal_auditors_count": internal_auditors_count,
        "process_owners_count": process_owners_count,
        "total_members": total_members,
        "members": members,
        "iso_clauses": iso_clauses,
        "non_conformities": non_conformities,
        'audit_details': audit_details,

    }

    return render(request, 'main/lead auditor/lead_auditor_dashboard.html', context)


@login_required
def internal_auditor_dashboard_view(request):
    # Get the total count of Non-Conformities
    total_non_conformities_count = NonConformity.objects.count()
    major_nc_count = NonConformity.objects.filter(category='major').count()
    minor_nc_count = NonConformity.objects.filter(category='minor').count()
    ofi_count = NonConformity.objects.filter(rfa_intent='improvement').count()
    good_points_count = AuditFinding.objects.filter(finding_type='Good Points').count()

    process_owners_count = UserProfile.objects.filter(role='Process Owner').count()

    non_conformities = NonConformity.objects.all()

    iso_clauses = {
        '4': "Context of the Organization",
        '5': "Leadership",
        '6': "Planning",
        '7': "Support",
        '8': "Operation",
        '9': "Performance Evaluation",
        '10': "Improvement",
    }

    # Fetch only Process Owners for the modal list
    process_owners = UserProfile.objects.filter(role='Process Owner').select_related('user')
    # Prepare context
    context = {
        "total_non_conformities_count": total_non_conformities_count,
        "major_nc_count": major_nc_count,
        "minor_nc_count": minor_nc_count,
        "ofi_count": ofi_count,
        "good_points_count": good_points_count,
        "process_owners_count": process_owners_count,
        "process_owners": process_owners,
        "iso_clauses": iso_clauses,
        "non_conformities": non_conformities
    }

    return render(request, 'main/internal audit/internal_auditor_dashboard.html', context)


@login_required
def process_owner_dashboard_view(request):
    """
    Dashboard view for Process Owners.
    Displays ONLY tasks and counts for tasks assigned to the logged-in user.
    """
    # Filter tasks assigned to the logged-in user
    user_tasks = NonConformity.objects.filter(assigned_to=request.user)

    # Task counts by status for the assigned user
    open_task_count = user_tasks.filter(status='open').count()
    pending_task_count = user_tasks.filter(status='pending').count()
    closed_task_count = user_tasks.filter(status='closed').count()

    # Task counts by category for the assigned user
    major_nc_count = user_tasks.filter(category='major').count()
    minor_nc_count = user_tasks.filter(category='minor').count()
    ofi_count = user_tasks.filter(category='ofi').count()

    # Pass all filtered data to the template
    context = {
        "tasks": user_tasks,  # All tasks assigned to the logged-in user
        "open_task_count": open_task_count,  # Open tasks count
        "pending_task_count": pending_task_count,  # Pending tasks count
        "closed_task_count": closed_task_count,  # Closed tasks count
        "major_nc_count": major_nc_count,  # Major NC count
        "minor_nc_count": minor_nc_count,  # Minor NC count
        "ofi_count": ofi_count,  # OFI count
    }

    return render(request, 'main/process owner/process_owner_dashboard.html', context)


logger = logging.getLogger(__name__)
@login_required
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password('sorsu123')  # Assign default password
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': form.cleaned_data['role'],
                    'password_needs_reset': True  # Force password reset
                }
            )
            messages.success(request, f'User "{user.username}" successfully added!')
            return redirect('lead_auditor_manage_user')
        else:
            print("Form validation errors:", form.errors)  # Debugging
            messages.error(request, 'Failed to add user. Please check the form.')
    return redirect('lead_auditor_manage_user')


@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()

            # Update the user's profile role if applicable
            user.userprofile.role = form.cleaned_data['role']
            user.userprofile.save()

            messages.success(request, 'User account has been successfully updated.')
            logger.info(f'User {user.username} updated successfully.')
            return redirect('lead_auditor_manage_user')
        else:
            messages.error(request, 'Please correct the errors below.')
            logger.error(f'Form validation failed. Errors: {form.errors}')
    else:
        form = UserUpdateForm(instance=user)

    context = {
        'edit_user_form': form,
        'user': user,
    }
    return render(request, 'main/lead auditor/lead_auditor_manage_user.html', context)


@login_required
def delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Ensure only superusers or the user themselves can delete the account
    if not (request.user.is_superuser or request.user == user):
        return HttpResponse('Unauthorized', status=403)

    if request.method == 'POST':
        try:
            # Log username before deletion
            username = user.username
            user.delete()
            messages.success(request, f'User "{username}" has been successfully deleted.')
            logger.info(f'User {username} was deleted by {request.user.username}.')
            return redirect('lead_auditor_manage_user')
        except Exception as e:
            logger.error(f'Error deleting user {user.username}: {e}')
            messages.error(request, 'An error occurred while deleting the user.')
            return redirect('lead_auditor_manage_user')

    # If it's not a POST request, return an error
    return HttpResponse('Invalid request method', status=405)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in after password change

            # Update the UserProfile and clear the `password_needs_reset` flag
            user_profile = request.user.userprofile  # Assuming a OneToOne relationship with the UserProfile
            user_profile.password_needs_reset = False
            user_profile.save()

            # Success message
            messages.success(request, 'Your profile and password have been successfully updated.')

            # Redirect based on the user's role
            if user_profile.role == 'Internal Auditor':
                return redirect('internal_auditor_dashboard')  # Ensure this URL name is defined
            elif user_profile.role == 'Process Owner':
                return redirect('process_owner_dashboard')
            elif user_profile.role == 'Lead Auditor':
                return redirect('lead_auditor_dashboard')
            else:
                return redirect('dashboard')  # Default redirect for other roles
        else:
            # Show error messages if the form is not valid
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill the form with the user's current first name and last name
        form = CustomPasswordChangeForm(user=request.user, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })

    return render(request, 'main/lead auditor/change_password.html', {'form': form})


def verify_email(request, token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        user = User.objects.get(email=email)
        user_profile = UserProfile.objects.get(user=user)
        user_profile.email_verified = True
        user_profile.save()
        messages.success(request, 'Email successfully verified.')
        return redirect('login')
    except SignatureExpired:
        messages.error(request, 'The verification link has expired.')
    except BadSignature:
        messages.error(request, 'The verification link is invalid.')
    except Exception as e:
        messages.error(request, 'An unexpected error occurred.')
    return redirect('login')


def role_allowed_to_manage_forms(user):
    """Check if user is Lead Auditor or Internal Auditor."""
    return hasattr(user, 'userprofile') and user.userprofile.role in ['Lead Auditor', 'Internal Auditor']


@login_required
@user_passes_test(role_allowed_to_manage_forms)
def manage_forms_view(request):
    """Unified view for Lead Auditor and Internal Auditor to manage forms."""
    templates = TemplateModel.objects.all()
    user_role = request.user.userprofile.role

    # Determine template to use based on role
    template = 'main/lead auditor/lead_auditor_forms.html' if user_role == 'Lead Auditor' else 'main/internal audit/internal_auditor_forms.html'

    return render(request, template, {'templates': templates})


@login_required
@user_passes_test(role_allowed_to_manage_forms)
def upload_template(request):
    """Unified view for uploading templates."""
    if request.method == 'POST':
        template_name = request.POST.get('template_name')
        template_description = request.POST.get('template_description')
        template_file = request.FILES.get('template_file')

        if template_file:
            template_model = TemplateModel.objects.create(
                template_name=template_name,
                description=template_description,
                file=template_file,
            )
            template_model.save()
            messages.success(request, "Template uploaded successfully.")
        else:
            messages.error(request, "No file was uploaded.")

        # Redirect based on role
        user_role = request.user.userprofile.role
        if user_role == 'Lead Auditor':
            return redirect('lead_auditor_forms')
        elif user_role == 'Internal Auditor':
            return redirect('internal_auditor_forms')
        else:
            return redirect('process_owner_forms')  # Default redirect for other roles

    # Redirect if not a POST request
    user_role = request.user.userprofile.role
    if user_role == 'Lead Auditor':
        return redirect('lead_auditor_forms')
    elif user_role == 'Internal Auditor':
        return redirect('internal_auditor_forms')
    else:
        return redirect('process_owner_forms')


@login_required
def download_template(request, pk):
    """View for downloading templates."""
    template = get_object_or_404(TemplateModel, pk=pk)
    if template.file:
        try:
            file = template.file.open('rb')
            response = FileResponse(file, as_attachment=True, filename=template.file.name)
            return response
        except FileNotFoundError:
            raise Http404("File not found.")
    return redirect('manage_forms')


@login_required
@user_passes_test(role_allowed_to_manage_forms)
def edit_template(request, pk):
    """View to edit an existing template."""
    template = get_object_or_404(TemplateModel, pk=pk)

    if request.method == 'POST':
        template.template_name = request.POST.get('template_name', template.template_name)
        template.description = request.POST.get('template_description', template.description)

        if 'template_file' in request.FILES:
            template.file = request.FILES['template_file']

        template.save()
        messages.success(request, "Template updated successfully.")

        # Redirect based on the user's role
        user_role = request.user.userprofile.role
        if user_role == 'Lead Auditor':
            return redirect('lead_auditor_forms')
        elif user_role == 'Internal Auditor':
            return redirect('internal_auditor_forms')
        else:
            return redirect('manage_forms')  # Default fallback

    # Default redirection for GET requests
    return redirect('manage_forms')


@login_required
@user_passes_test(role_allowed_to_manage_forms)
def delete_template(request, pk):
    """View for deleting templates."""
    template = get_object_or_404(TemplateModel, pk=pk)

    if request.method == "POST":
        if template.file:
            template.file.delete(save=False)
        template.delete()
        messages.success(request, "Template deleted successfully.")
    else:
        messages.error(request, "Delete request must be POST.")

    # Redirect the user back to their appropriate forms page
    if request.user.userprofile.role == 'Lead Auditor':
        return redirect('lead_auditor_forms')
    elif request.user.userprofile.role == 'Internal Auditor':
        return redirect('internal_auditor_forms')
    return redirect('process_owner_forms')  # Default redirect


@login_required
def process_owner_forms_view(request):
    """View for Process Owner to view and download forms."""
    templates = TemplateModel.objects.all()
    return render(request, 'main/process owner/process_owner_forms.html', {'templates': templates})


@login_required
def internal_auditor_monitoring_log(request):
    # Retrieve all non-conformities with prefetching to optimize queries
    non_conformities = NonConformity.objects.prefetch_related(
        Prefetch('corrective_action_plans__action_verifications')
    ).all()

    # Count non-conformities based on statuses
    open_count = non_conformities.filter(status='open').count()
    pending_count = non_conformities.filter(status='pending').count()
    closed_count = non_conformities.filter(status='closed').count()
    total_count = non_conformities.count()

    context = {
        'non_conformities': non_conformities,
        'open_count': open_count,       # Count of 'Open' status
        'pending_count': pending_count, # Count of 'Pending' status
        'closed_count': closed_count,   # Count of 'Closed' status
        'total_count': total_count,     # Total count of non-conformities
    }
    return render(request, 'main/internal audit/internal_auditor_monitoring_log.html', context)


# Check if user is internal auditor
def is_internal_auditor(user):
    return hasattr(user, 'userprofile') and user.userprofile.role == 'Internal Auditor'


@login_required
def guideline_management_view(request):
    """Unified view to handle guideline management for all roles."""
    role = request.user.userprofile.role
    template = None

    # Set the template and permissions based on the role
    if role == 'Lead Auditor':
        template = 'main/lead auditor/lead_auditor_guidelines.html'
    elif role == 'Internal Auditor':
        template = 'main/internal audit/internal_auditor_guidelines.html'
    elif role == 'Process Owner':
        template = 'main/process owner/list.html'
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    # Fetch guidelines for viewing
    guidelines = Guideline.objects.all()

    # Handle form submissions (CRUD actions)
    if request.method == 'POST':
        action = request.POST.get('action')  # Action can be 'add', 'edit', 'delete'
        if action == 'add' and role in ['Lead Auditor', 'Internal Auditor']:
            form = GuidelineForm(request.POST, request.FILES)
            if form.is_valid():
                guideline = form.save(commit=False)
                guideline.uploaded_by = request.user
                guideline.save()
                messages.success(request, "Guideline added successfully.")
            else:
                messages.error(request, "Failed to add guideline. Please check the form.")
        elif action == 'edit' and role in ['Lead Auditor', 'Internal Auditor']:
            guideline_id = request.POST.get('guideline_id')
            guideline = get_object_or_404(Guideline, id=guideline_id)
            form = GuidelineForm(request.POST, request.FILES, instance=guideline)
            if form.is_valid():
                form.save()
                messages.success(request, "Guideline updated successfully.")
            else:
                messages.error(request, "Failed to update guideline. Please check the form.")
        elif action == 'delete' and role in ['Lead Auditor', 'Internal Auditor']:
            guideline_id = request.POST.get('guideline_id')
            guideline = get_object_or_404(Guideline, id=guideline_id)
            guideline.delete()
            messages.success(request, "Guideline deleted successfully.")
        else:
            messages.error(request, "Invalid action or insufficient permissions.")

        return redirect(request.path)  # Refresh the page after form submission

    # Provide a blank form for adding a new guideline
    form = GuidelineForm()

    context = {
        'guidelines': guidelines,
        'form': form,
        'role': role,  # Pass role to the template for role-specific UI elements
    }

    return render(request, template, context)


@login_required
def add_non_conformity(request):
    # Restrict access to Lead Auditors only
    if request.user.userprofile.role != 'Lead Auditor':
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == 'POST':
        # Get form data
        non_conformity = request.POST.get('non_conformity')
        unit_department = request.POST.get('unit_department')
        rfa_intent = request.POST.get('rfa_intent')
        non_conformance_category = request.POST.get('non_conformance_category')
        description_of_non_conformance = request.POST.get('description_of_non_conformance')
        iso_clause = request.POST.get('iso_clause')
        category = request.POST.get('category')
        assigned_to_id = request.POST.get('assigned_to')  # Process Owner ID from form

        # Get the assigned Process Owner
        assigned_to = User.objects.get(id=assigned_to_id)

        # Create the NonConformity instance
        non_conformity_instance = NonConformity.objects.create(
            non_conformity=non_conformity,
            assignees=assigned_to.username,
            originator_name=request.user.get_full_name(),  # Auto-fill originator's name
            unit_department=unit_department,
            rfa_intent=rfa_intent,
            non_conformance_category=non_conformance_category,
            description_of_non_conformance=description_of_non_conformance,
            iso_clause=iso_clause,
            category=category,
            assigned_to=assigned_to,
            status='open'  # Default status
        )

        # Generate the URL for the non-conformity using its get_task_url method
        url = non_conformity_instance.get_task_url()
        print(f"Generated URL: {url}")  # Debugging

        # Send notification to the assigned Process Owner
        notify.send(
            request.user,  # The user creating the Non-Conformity (Lead Auditor)
            recipient=assigned_to,  # Process Owner
            verb="New Task Assigned",
            description=f"You have been assigned a new Non-Conformity: {non_conformity_instance.non_conformity}.",
            target=non_conformity_instance  # Link to the created Non-Conformity
        )

        # Retrieve the notification instance
        notification = Notification.objects.filter(
            recipient=assigned_to,
            verb="New Task Assigned",
            target_object_id=non_conformity_instance.id  # Use the NonConformity instance's ID
        ).order_by('-timestamp').first()

        if notification:
            # Add the URL to the notification data field manually
            notification.data = {'url': non_conformity_instance.get_task_url()}
            notification.save()
            print(f"Notification saved with data: {notification.data}")
        else:
            print("Notification instance not found. Data was not added.")

        # Add success message and redirect
        messages.success(request, 'Non-Conformity successfully created and Process Owner notified.')

        # Redirect to Lead Auditor's monitoring log
        return redirect('lead_auditor_monitoring_log')

    # Fetch all Process Owners for dropdown in the form
    process_owners = User.objects.filter(userprofile__role='Process Owner')

    # Render the appropriate template
    return render(request, 'main/lead auditor/add_non_conformity.html', {
        'process_owners': process_owners
    })

@login_required
def combined_non_conformity_detail(request, nc_id):
    # Determine the current view name based on the request path
    current_view_name = resolve(request.path).url_name  # Get the name of the current view
    is_lead_auditor = current_view_name == 'lead_auditor_non_conformity_detail'

    # Fetch the non-conformity record
    non_conformity = get_object_or_404(NonConformity, id=nc_id)

    # Existing data fetching
    immediate_action = ImmediateAction.objects.filter(non_conformity=non_conformity).first()
    root_cause_analysis = RootCauseAnalysis.objects.filter(non_conformity=non_conformity).first()
    corrective_action_plans = CorrectiveActionPlan.objects.filter(non_conformity=non_conformity)
    corrective_action_plan = corrective_action_plans.first()
    follow_up_actions = FollowUpAction.objects.filter(non_conformity=non_conformity).order_by('-follow_up_date')

    if corrective_action_plan:
        action_verifications = ActionVerification.objects.filter(
            corrective_action_plan=corrective_action_plan
        ).order_by('-date')
    else:
        action_verifications = None

    latest_review = CorrectiveActionPlanReview.objects.filter(
        corrective_action_plan__non_conformity=non_conformity
    ).order_by('-review_date').first()

    # Fetch comments for each section
    immediate_action_comments = Comment.objects.filter(
        task=non_conformity, section='immediate_action', parent__isnull=True
    ).order_by('-created_at')
    root_cause_comments = Comment.objects.filter(
        task=non_conformity, section='root_cause_analysis', parent__isnull=True
    ).order_by('-created_at')
    corrective_action_comments = Comment.objects.filter(
        task=non_conformity, section='corrective_action_plan', parent__isnull=True
    ).order_by('-created_at')

    # Handle POST request for adding/deleting comments
    if request.method == 'POST':
        if 'delete_comment_id' in request.POST:
            comment_id = request.POST.get('delete_comment_id')
            comment_to_delete = Comment.objects.filter(id=comment_id, author=request.user).first()
            if comment_to_delete:
                comment_to_delete.delete()
                messages.success(request, "Comment deleted successfully!")
            else:
                messages.error(request, "You do not have permission to delete this comment.")
        elif 'comment_content' in request.POST:
            content = request.POST.get('comment_content', '').strip()
            section = request.POST.get('section', '').strip()
            parent_id = request.POST.get('parent_id')  # Parent comment ID for replies

            if content and section in ['immediate_action', 'root_cause_analysis', 'corrective_action_plan']:
                parent_comment = Comment.objects.filter(id=parent_id).first() if parent_id else None
                Comment.objects.create(
                    task=non_conformity,
                    author=request.user,
                    content=content,
                    section=section,
                    parent=parent_comment
                )
                messages.success(request, "Comment added successfully!")
            else:
                messages.error(request, "Comment content or section is invalid.")

            # Redirect to prevent duplicate submissions
            return redirect(current_view_name, nc_id=nc_id)

    # Prepare context for rendering
    context = {
        'non_conformity': non_conformity,
        'immediate_action': immediate_action,
        'root_cause_analysis': root_cause_analysis,
        'corrective_action_plans': corrective_action_plans,
        'corrective_action_plan': corrective_action_plan,
        'follow_up_actions': follow_up_actions,
        'verifications': action_verifications,
        'latest_review': latest_review,
        'immediate_action_comments': immediate_action_comments,
        'root_cause_comments': root_cause_comments,
        'corrective_action_comments': corrective_action_comments,
        'is_lead_auditor': is_lead_auditor,
    }

    # Render different templates or modify behavior based on role or path
    if is_lead_auditor:
        return render(request, 'main/lead auditor/non_conformity_detail.html', context)
    else:
        return render(request, 'main/internal audit/non_conformity_detail.html', context)


@login_required
def task_detail(request, task_id):
    # Fetch the task (Non-Conformity record)
    task = get_object_or_404(NonConformity, id=task_id)

    # Fetch related comments for each section
    immediate_action_comments = Comment.objects.filter(
        task=task, section='immediate_action', parent__isnull=True
    ).order_by('-created_at')
    root_cause_comments = Comment.objects.filter(
        task=task, section='root_cause_analysis', parent__isnull=True
    ).order_by('-created_at')
    corrective_action_comments = Comment.objects.filter(
        task=task, section='corrective_action_plan', parent__isnull=True
    ).order_by('-created_at')

    # Fetch related data
    immediate_action = ImmediateAction.objects.filter(non_conformity=task).first()
    root_cause_analysis = RootCauseAnalysis.objects.filter(non_conformity=task).first()
    corrective_action_plans = CorrectiveActionPlan.objects.filter(non_conformity=task)

    # Handle POST request for adding/replying to comments or deleting them
    if request.method == 'POST':
        if 'delete_comment_id' in request.POST:
            # Handle comment deletion
            comment_id = request.POST.get('delete_comment_id')
            comment_to_delete = Comment.objects.filter(id=comment_id, author=request.user).first()
            if comment_to_delete:
                comment_to_delete.delete()
                messages.success(request, "Comment deleted successfully!")
            else:
                messages.error(request, "You do not have permission to delete this comment.")
        elif 'comment_content' in request.POST:
            # Handle adding a new comment or reply
            content = request.POST.get('comment_content', '').strip()
            section = request.POST.get('section', '').strip()
            parent_id = request.POST.get('parent_id')  # ID of the parent comment (if replying)

            if content and section in ['immediate_action', 'root_cause_analysis', 'corrective_action_plan']:
                parent_comment = Comment.objects.filter(id=parent_id).first() if parent_id else None
                Comment.objects.create(
                    task=task,
                    author=request.user,
                    content=content,
                    section=section,
                    parent=parent_comment
                )
                messages.success(request, "Comment added successfully!")
            else:
                messages.error(request, "Comment content or section is invalid.")

            # Redirect back to task_detail view to prevent duplicate submissions
            return redirect('task_detail', task_id=task_id)

    # Context for rendering the template
    context = {
        'task': task,
        'immediate_action': immediate_action,
        'root_cause_analysis': root_cause_analysis,
        'corrective_action_plans': corrective_action_plans,
        'immediate_action_comments': immediate_action_comments,
        'root_cause_comments': root_cause_comments,
        'corrective_action_comments': corrective_action_comments,
    }

    return render(request, 'main/process owner/task_detail.html', context)


from django.contrib.auth.decorators import login_required

@login_required
def add_immediate_action(request, task_id):
    task = get_object_or_404(NonConformity, id=task_id)

    # Ensure the user is a Process Owner
    if not request.user.userprofile.role == 'Process Owner':
        return HttpResponseForbidden("You do not have permission to add an immediate action.")

    if request.method == 'POST':
        # Get or create the ImmediateAction instance
        immediate_action, created = ImmediateAction.objects.get_or_create(non_conformity=task)

        # Update the action description
        immediate_action.action_description = request.POST.get('immediate_action')

        # Retrieve the full names of all process owners
        process_owners = UserProfile.objects.filter(role='Process Owner')
        acknowledged_names = ', '.join(
            [f"{profile.user.first_name} {profile.user.last_name}" for profile in process_owners]
        )

        # Save the full names in the acknowledged_by field
        immediate_action.acknowledged_by = acknowledged_names

        # Set the acknowledgment date to the current date
        immediate_action.acknowledgment_date = now().date()

        # Save the updated ImmediateAction instance
        immediate_action.save()

        # Notify Lead and Internal Auditors
        lead_users = UserProfile.objects.filter(role='Lead Auditor')
        internal_auditors = UserProfile.objects.filter(role='Internal Auditor')

        # Send email notifications (optional)
        for user_profile in lead_users.union(internal_auditors):
            send_mail(
                'New Immediate Action Added',
                f'An immediate action has been added for task: {task.non_conformity}. Please review it.',
                'from@example.com',  # Use your 'from' email
                [user_profile.user.email],
                fail_silently=False,
            )

            # Create in-app notifications for the users
            notify.send(
                request.user,  # sender
                recipient=user_profile.user,  # recipient
                verb=f'An immediate action has been added for task: {task.non_conformity}. Please review it.',  # action description
                target=task,  # target object (task)
                action_object=immediate_action  # action object (immediate action)
            )

        messages.success(request, "Immediate Action saved successfully.")
        return redirect('task_detail', task_id=task.id)  # Ensure the redirect goes to task detail

    # Handle invalid request
    messages.error(request, "Invalid request.")
    return redirect('task_detail', task_id=task.id)  # Redirect to task detail even if the request is invalid



# View for saving Root Cause Analysis
@login_required
def add_root_cause_analysis(request, task_id):
    task = get_object_or_404(NonConformity, id=task_id)

    if request.method == 'POST':
        root_cause_analysis, created = RootCauseAnalysis.objects.get_or_create(non_conformity=task)

        # Save data from the form
        root_cause_analysis.cause_description = request.POST.get('root_cause', '')
        root_cause_analysis.rca_date = request.POST.get('rca_date')
        root_cause_analysis.responsible_officer = request.POST.get('responsible_officer', '')
        root_cause_analysis.estimated_close_date = request.POST.get('estimated_close_date')
        root_cause_analysis.supporting_evidence = request.POST.get('supporting_evidence', '')

        # Handle supporting evidence upload
        if 'supporting_evidence' in request.FILES:
            print("File received:", request.FILES['supporting_evidence'].name)
            root_cause_analysis.supporting_evidence = request.FILES['supporting_evidence']
        else:
            print("No file received")

        # Validate required fields
        if not root_cause_analysis.cause_description or not root_cause_analysis.rca_date:
            messages.error(request, "Root cause description and date are required.")
            return redirect('task_detail', task_id=task.id)

        # Save the updated root cause analysis
        root_cause_analysis.save()

        # Notify Lead and Internal Auditors
        lead_users = UserProfile.objects.filter(role='Lead Auditor')
        internal_auditors = UserProfile.objects.filter(role='Internal Auditor')

        # Send email notifications
        for user_profile in lead_users.union(internal_auditors):
            send_mail(
                'New Root Cause Analysis Created',
                f'A root cause analysis has been created for task: {task.non_conformity}. Please review it.',
                'from@example.com',  # Replace with the sender's email
                [user_profile.user.email],
                fail_silently=False,
            )

            # Create in-app notifications for the users
            notify.send(
                request.user,  # sender (Process Owner)
                recipient=user_profile.user,  # recipient (Lead or Internal Auditor)
                verb=f'A root cause analysis has been created for task: {task.non_conformity}. Please review it.',  # action description
                target=task,  # target object (NonConformity)
                action_object=root_cause_analysis  # action object (RootCauseAnalysis)
            )

        # Provide success message and redirect to task details
        messages.success(request, "Root Cause Analysis saved successfully.")
        return redirect('task_detail', task_id=task.id)

    # If the request method is not POST
    messages.error(request, "Invalid request.")
    return redirect('task_detail', task_id=task.id)



@login_required
def corrective_action_plan(request, task_id):
    task = get_object_or_404(NonConformity, id=task_id)

    if request.method == 'POST':
        # Remove existing plans only if necessary
        CorrectiveActionPlan.objects.filter(non_conformity=task).delete()

        # Save multiple plans
        row_count = len([key for key in request.POST.keys() if key.startswith('activity_')])
        for i in range(1, row_count + 1):
            corrective_action_plan = CorrectiveActionPlan.objects.create(
                non_conformity=task,
                activity=request.POST.get(f'activity_{i}'),
                responsible_person=request.POST.get(f'responsible_person_{i}'),
                time_frame=request.POST.get(f'time_frame_{i}'),
                resources_needed=request.POST.get(f'resources_needed_{i}'),
                result=request.POST.get(f'result_{i}', '')
            )

        # Notify Lead and Internal Auditors
        lead_users = UserProfile.objects.filter(role='Lead Auditor')
        internal_auditors = UserProfile.objects.filter(role='Internal Auditor')

        # Send email notifications (optional)
        for user_profile in lead_users.union(internal_auditors):
            send_mail(
                'New Corrective Action Plan Created',
                f'A corrective action plan has been created for task: {task.non_conformity}. Please review it.',
                'from@example.com',  # Use your 'from' email
                [user_profile.user.email],
                fail_silently=False,
            )

            # Create in-app notifications for the users
            notify.send(
                request.user,  # sender
                recipient=user_profile.user,  # recipient
                verb=f'A corrective action plan has been created for task: {task.non_conformity}. Please review it.',  # action description
                target=task,  # target object (task)
                action_object=corrective_action_plan  # action object (corrective action plan)
            )

        messages.success(request, "Corrective Action Plans saved successfully.")
        return redirect('task_detail', task_id=task.id)

    # Fetch corrective action plans
    corrective_action_plans = CorrectiveActionPlan.objects.filter(non_conformity=task)
    return render(request, 'main/internal audit/non_conformity_detail.html', {
        'non_conformity': task,
        'corrective_action_plans': corrective_action_plans,
    })


@login_required
def add_review(request, cap_id):
    corrective_action_plan = get_object_or_404(CorrectiveActionPlan, id=cap_id)
    non_conformity = corrective_action_plan.non_conformity

    # Get the user's role from the UserProfile model
    user_role = getattr(request.user.userprofile, 'role', None)
    allowed_roles = ['Lead Auditor', 'Internal Auditor']  # Roles allowed to add a review

    # Validate the user's role
    if user_role not in allowed_roles:
        raise PermissionDenied("You do not have permission to add a review.")

    if request.method == 'POST':
        effectiveness = request.POST.get('effectiveness')
        reason = request.POST.get('reason', '')  # Optional field
        restart_process = effectiveness == 'Not Accepted'

        # Create a new review
        CorrectiveActionPlanReview.objects.create(
            corrective_action_plan=corrective_action_plan,
            reviewer=request.user,
            effectiveness=effectiveness,
            reason=reason,
            restart_process=restart_process
        )

        if restart_process:
            # Create a new RFA
            new_rfa = NonConformity.objects.create(
                non_conformity=f"New RFA for: {non_conformity.non_conformity}",
                assignees=non_conformity.assignees,
                originator_name=non_conformity.originator_name,
                unit_department=non_conformity.unit_department,
                phone=non_conformity.phone,
                email=non_conformity.email,
                rfa_intent=non_conformity.rfa_intent,
                department=non_conformity.department,
                non_conformance_category=non_conformity.non_conformance_category,
                description_of_non_conformance=non_conformity.description_of_non_conformance,
                iso_clause=non_conformity.iso_clause,
                category=non_conformity.category,
                start_date=now().date(),
                status='pending',
                assigned_to=non_conformity.assigned_to
            )
            messages.warning(
                request,
                f"Corrective Action Plan rejected. A new RFA was issued: {new_rfa.non_conformity}."
            )
        else:
            messages.success(request, "Review added successfully.")

            # Notify the Process Owner
            if non_conformity.assigned_to:  # Check if a process owner is assigned
                notify.send(
                    sender=request.user,
                    recipient=non_conformity.assigned_to,
                    verb="New Review Added",
                    description=f"A review was added to the corrective action plan for {non_conformity.non_conformity}.",
                    target=corrective_action_plan
                )

        # Redirect based on the user's role
        if user_role == 'Lead Auditor':
            return redirect('lead_auditor_non_conformity_detail', nc_id=non_conformity.id)
        else:
            return redirect('non_conformity_detail', nc_id=non_conformity.id)

    # Handle other methods (e.g., GET) by redirecting to the detail page
    if user_role == 'Lead Auditor':
        return redirect('lead_auditor_non_conformity_detail', nc_id=non_conformity.id)
    else:
        return redirect('non_conformity_detail', nc_id=non_conformity.id)


@login_required
def add_follow_up(request, nc_id):
    # Get the Non-Conformity record
    non_conformity = get_object_or_404(NonConformity, id=nc_id)

    # Determine the current view name based on the request path
    current_view_name = resolve(request.path).url_name
    is_lead_auditor = current_view_name == 'lead_auditor_add_follow_up'

    if request.method == 'POST':
        form = FollowUpActionForm(request.POST)
        if form.is_valid():
            follow_up = form.save(commit=False)
            follow_up.non_conformity = non_conformity  # Associate follow-up with the non-conformity
            follow_up.save()
            messages.success(request, "Follow-Up Action added successfully.")
            # Redirect based on role
            if is_lead_auditor:
                return redirect('lead_auditor_non_conformity_detail', nc_id=nc_id)
            else:
                return redirect('non_conformity_detail', nc_id=nc_id)
        else:
            messages.error(request, "Error saving Follow-Up Action. Please try again.")
    else:
        form = FollowUpActionForm()

    follow_up_actions = FollowUpAction.objects.filter(non_conformity=non_conformity).order_by('-follow_up_date')

    # Context for rendering
    context = {
        'form': form,
        'follow_up_actions': follow_up_actions,
        'non_conformity': non_conformity,
        'is_lead_auditor': is_lead_auditor,  # Pass role context if needed for templates
    }

    # Render the appropriate template based on the role
    if is_lead_auditor:
        return render(request, 'main/lead auditor/non_conformity_detail.html', context)
    else:
        return render(request, 'main/internal audit/non_conformity_detail.html', context)


from notifications.signals import notify


@login_required
def action_verification(request, cap_id):
    try:
        # Fetch the Corrective Action Plan and associated Non-Conformity
        corrective_action_plan = get_object_or_404(CorrectiveActionPlan, id=cap_id)
        non_conformity = corrective_action_plan.non_conformity
    except CorrectiveActionPlan.DoesNotExist:
        messages.error(request, f"No Corrective Action Plan found with ID: {cap_id}")
        return redirect('non_conformity_list')

    # Determine if the current user is a lead auditor
    current_view_name = resolve(request.path).url_name
    is_lead_auditor = current_view_name == 'lead_auditor_action_verification'

    # Fetch verifications related to the Corrective Action Plan
    verifications = ActionVerification.objects.filter(corrective_action_plan=corrective_action_plan).order_by('-date')

    def generate_notification_url(view_name, args):
        """
        Generates and validates a notification URL.
        Returns a valid URL or raises an exception for debugging.
        """
        try:
            # Generate the URL
            url = reverse(view_name, args=args)
            # Ensure the URL resolves to an actual view
            resolve(url)
            return url
        except (Http404, Exception) as e:
            print(f"Error generating or resolving URL: {e}")  # Debugging
            raise ValueError("Invalid URL or view does not exist")

    if request.method == 'POST':
        # Handle form submissions
        verification_form = ActionVerificationForm(request.POST)
        evaluation_form = EvaluationForm(request.POST)

        if verification_form.is_valid():
            verification = verification_form.save(commit=False)
            verification.corrective_action_plan = corrective_action_plan
            verification.save()

            # Handle effective verification
            if verification.status == "effective":
                CloseOut.objects.update_or_create(
                    non_conformity=non_conformity,
                    defaults={
                        'auditor_name': request.user.get_full_name() or request.user.username,
                        'auditor_date': verification.date,
                        'process_owner_name': non_conformity.assigned_to.get_full_name() if non_conformity.assigned_to else "Unknown",
                        'process_owner_date': verification.date,
                    }
                )
                messages.success(request, "Corrective action verified as effective. Close Out record updated.")

                process_owner = non_conformity.assigned_to
                if process_owner:
                    try:
                        # Generate and validate the evaluation form URL
                        url = reverse('evaluation_form', args=[verification.id])
                        resolve(url)  # Ensure the URL resolves correctly
                        print(f"Notification URL: {url}")  # Debugging

                        # Send the notification
                        notify.send(
                            sender=request.user,
                            recipient=process_owner,
                            verb="Action Effective",
                            description=f"Corrective action plan for '{non_conformity.non_conformity}' has been marked as effective. Please proceed to evaluation.",
                            target=verification
                        )

                        # Retrieve the notification instance
                        notification = Notification.objects.filter(
                            recipient=process_owner,
                            verb="Action Effective",
                            target_object_id=verification.id
                        ).order_by('-timestamp').first()

                        if notification:
                            # Add the URL to the notification data field manually
                            notification.data = {'url': url}
                            notification.save()
                            print(f"Notification saved with data: {notification.data}")
                        else:
                            print("Notification instance not found. Data was not added.")

                    except Exception as e:
                        print(f"Error generating or sending notification: {e}")
                        messages.error(request, "Failed to send notification. Please try again.")

                else:
                    messages.warning(request,
                                     "Verification is effective, but no process owner is assigned to the non-conformity.")

            # Handle not effective status
            elif verification.status == "not effective":
                process_owner = non_conformity.assigned_to
                if process_owner:
                    notify.send(
                        sender=request.user,
                        recipient=process_owner,
                        verb="Action Not Effective",
                        description=f"Corrective action plan for '{non_conformity.non_conformity}' was deemed not effective.",
                        target=verification
                    )
                    # Create a new RFA (Request for Action)
                    NonConformity.objects.create(
                        non_conformity=f"New RFA for: {non_conformity.non_conformity}",
                        assignees=non_conformity.assignees,
                        originator_name=non_conformity.originator_name,
                        unit_department=non_conformity.unit_department,
                        phone=non_conformity.phone,
                        email=non_conformity.email,
                        rfa_intent=non_conformity.rfa_intent,
                        department=non_conformity.department,
                        non_conformance_category=non_conformity.non_conformance_category,
                        description_of_non_conformance=non_conformity.description_of_non_conformance,
                        iso_clause=non_conformity.iso_clause,
                        category=non_conformity.category,
                        start_date=now().date(),
                        status='pending',
                        assigned_to=process_owner
                    )
                    messages.warning(request, "Corrective action plan deemed not effective. A new RFA has been issued.")

            # Redirect based on user role
            return redirect(
                'lead_auditor_non_conformity_detail' if is_lead_auditor else 'non_conformity_detail',
                nc_id=non_conformity.id
            )

    else:
        # Handle GET request
        verification_form = ActionVerificationForm()
        evaluation_form = EvaluationForm()

        # Determine if evaluation form should be displayed
        display_evaluation_form = False
        if verifications.exists():
            last_verification = verifications.first()
            if last_verification.status == "effective" and non_conformity.assigned_to == request.user:
                display_evaluation_form = True

    context = {
        'corrective_action_plan': corrective_action_plan,
        'non_conformity': non_conformity,
        'verifications': verifications,
        'verification_form': verification_form,
        'evaluation_form': evaluation_form,
        'is_lead_auditor': is_lead_auditor,
        'display_evaluation_form': display_evaluation_form,
    }

    # Render the appropriate template
    return render(
        request,
        'main/lead auditor/non_conformity_detail.html' if is_lead_auditor else 'main/non_conformity_detail.html',
        context
    )


@login_required
def close_out_action(request, nc_id):
    try:
        # Fetch the Non-Conformity record
        non_conformity = get_object_or_404(NonConformity, id=nc_id)

        if request.method == 'POST':
            # Retrieve the data from the POST request
            auditor_name = request.POST.get('auditor_name')
            auditor_date = request.POST.get('auditor_date')

            # Validate required fields
            if not auditor_name or not auditor_date:
                messages.error(request, "All fields are required for Close Out.")
                return redirect('non_conformity_detail', nc_id=nc_id)

            # Save the Close Out data
            close_out, created = CloseOut.objects.get_or_create(non_conformity=non_conformity)
            close_out.auditor_name = auditor_name
            close_out.auditor_date = auditor_date
            close_out.process_owner_name = request.POST.get('process_owner_name', '')
            close_out.process_owner_date = request.POST.get('process_owner_date', '')
            close_out.save()

            # Success message and redirect
            messages.success(request, "Close Out data saved successfully.")
            return redirect('non_conformity_detail', nc_id=nc_id)
        else:
            # Redirect back if not a POST request
            return redirect('non_conformity_detail', nc_id=nc_id)

    except Exception as e:
        print(f"Error in close_out_action: {e}")
        return HttpResponseServerError("An error occurred while processing your request.")


@login_required
def evaluation_form(request, verification_id):
    # Fetch the verification and related non-conformity
    verification = get_object_or_404(ActionVerification, id=verification_id)

    # Check if an evaluation already exists for this verification
    evaluation_instance = Evaluation.objects.filter(action_verification=verification, evaluator=request.user).first()

    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=evaluation_instance)  # Pass existing instance if available
        if form.is_valid():
            # Save the evaluation
            evaluation = form.save(commit=False)
            evaluation.action_verification = verification
            evaluation.evaluator = request.user
            evaluation.save()

            messages.success(request, "Evaluation submitted successfully.")
            return redirect('process_owner_dashboard')  # Redirect after successful submission
    else:
        form = EvaluationForm(instance=evaluation_instance)  # Populate the form with existing data if available

    # Group fields by sections for the template
    grouped_fields = {
        'A': [
            {'field_name': 'knowledge1',
             'label': 'The internal auditor demonstrates understanding of ISO 9001:2015 requirements.',
             'choices': form['knowledge1'].field.choices, 'value': form['knowledge1'].value()},
            {'field_name': 'knowledge2', 'label': 'The internal auditor applies knowledge effectively during audits.',
             'choices': form['knowledge2'].field.choices, 'value': form['knowledge2'].value()},
            {'field_name': 'knowledge3', 'label': 'The internal auditor stays updated on changes to the standard.',
             'choices': form['knowledge3'].field.choices, 'value': form['knowledge3'].value()},
            {'field_name': 'knowledge4',
             'label': 'The internal auditor demonstrates proficiency in ISO audit requirements.',
             'choices': form['knowledge4'].field.choices, 'value': form['knowledge4'].value()},
            {'field_name': 'knowledge5',
             'label': 'The internal auditor ensures alignment with ISO standards in audit practices.',
             'choices': form['knowledge5'].field.choices, 'value': form['knowledge5'].value()},
        ],
        'B': [
            {'field_name': 'communication1', 'label': 'The internal auditor communicates effectively with auditees.',
             'choices': form['communication1'].field.choices, 'value': form['communication1'].value()},
            {'field_name': 'communication2',
             'label': 'The internal auditor listens actively and asks relevant questions.',
             'choices': form['communication2'].field.choices, 'value': form['communication2'].value()},
            {'field_name': 'communication3', 'label': 'The internal auditor provides clear and constructive feedback.',
             'choices': form['communication3'].field.choices, 'value': form['communication3'].value()},
            {'field_name': 'communication4',
             'label': 'The internal auditor demonstrates proficiency in written and verbal communication.',
             'choices': form['communication4'].field.choices, 'value': form['communication4'].value()},
            {'field_name': 'communication5',
             'label': 'The internal auditor facilitates open and transparent communication during audits.',
             'choices': form['communication5'].field.choices, 'value': form['communication5'].value()},
        ],
        'C': [
            {'field_name': 'audit_execution1', 'label': 'The internal auditor follows the established audit process.',
             'choices': form['audit_execution1'].field.choices, 'value': form['audit_execution1'].value()},
            {'field_name': 'audit_execution2',
             'label': 'The internal auditor demonstrates professionalism and objectivity.',
             'choices': form['audit_execution2'].field.choices, 'value': form['audit_execution2'].value()},
            {'field_name': 'audit_execution3',
             'label': 'The internal auditor adapts to unexpected situations during audits.',
             'choices': form['audit_execution3'].field.choices, 'value': form['audit_execution3'].value()},
            {'field_name': 'audit_execution4',
             'label': 'The internal auditor uses effective questioning techniques to gather information.',
             'choices': form['audit_execution4'].field.choices, 'value': form['audit_execution4'].value()},
            {'field_name': 'audit_execution5',
             'label': 'The internal auditor demonstrates a keen attention to detail during the audit process.',
             'choices': form['audit_execution5'].field.choices, 'value': form['audit_execution5'].value()},
        ],
        'E': [
            {'field_name': 'continual_improvement1',
             'label': 'The internal auditor actively seeks feedback and identifies areas for personal improvement.',
             'choices': form['continual_improvement1'].field.choices, 'value': form['continual_improvement1'].value()},
            {'field_name': 'continual_improvement2',
             'label': 'The internal auditor contributes to the improvement of the university\'s quality management system.',
             'choices': form['continual_improvement2'].field.choices, 'value': form['continual_improvement2'].value()},
            {'field_name': 'continual_improvement3',
             'label': 'The internal auditor encourages a culture of continuous improvement within the team.',
             'choices': form['continual_improvement3'].field.choices, 'value': form['continual_improvement3'].value()},
            {'field_name': 'continual_improvement4',
             'label': 'The internal auditor demonstrates a proactive approach to professional development.',
             'choices': form['continual_improvement4'].field.choices, 'value': form['continual_improvement4'].value()},
            {'field_name': 'continual_improvement5',
             'label': 'The internal auditor integrates lessons learned from previous audits into current practices.',
             'choices': form['continual_improvement5'].field.choices, 'value': form['continual_improvement5'].value()},
        ],
    }

    return render(request, 'main/process owner/evaluation.html', {
        'evaluation_form': form,
        'verification': verification,
        'grouped_fields': grouped_fields,
    })

@login_required
def complete_step(request, task_id):
    task = get_object_or_404(NonConformity, id=task_id)

    if request.method == 'POST':
        # Mark the task as completed
        task.status = 'completed'
        task.save()
        messages.success(request, "Step marked as completed successfully.")

    return redirect('non_conformity_detail', nc_id=task_id)


@login_required
def preview_rfa(request, nc_id):
    # Determine the current view name based on the request path
    current_view_name = resolve(request.path).url_name  # Get the name of the current view
    is_lead_auditor = current_view_name == 'lead_auditor_preview_rfa'

    # Fetch the NonConformity object by its ID
    non_conformity = get_object_or_404(NonConformity, id=nc_id)

    # Fetch related data
    immediate_action = ImmediateAction.objects.filter(non_conformity=non_conformity).first()
    root_cause_analysis = RootCauseAnalysis.objects.filter(non_conformity=non_conformity).first()
    corrective_action_plans = CorrectiveActionPlan.objects.filter(non_conformity=non_conformity)
    follow_up_actions = FollowUpAction.objects.filter(non_conformity=non_conformity)
    close_out = getattr(non_conformity, 'close_out', None)

    action_verifications = ActionVerification.objects.filter(
        corrective_action_plan__in=corrective_action_plans
    )

    reviews = []
    for cap in corrective_action_plans:
        review = cap.reviews.last()  # Fetch the latest review for each CAP, if any
        reviews.append({
            'effectiveness': review.effectiveness if review else "N/A",
            'reason': review.reason if review and review.reason else "N/A",
            'reviewer': review.reviewer.get_full_name() if review and review.reviewer else "N/A",
            'review_date': review.review_date if review else "N/A"
        })

    # Prepare the context
    context = {
        'non_conformity': non_conformity,
        'immediate_action': immediate_action,
        'root_cause_analysis': root_cause_analysis,
        'corrective_action_plans': corrective_action_plans,
        'reviews': reviews,
        'follow_up_actions': follow_up_actions,
        'action_verifications': action_verifications,
        'close_out': close_out,
        'left_logo_url': static('main/iso-sorsu-logo.png'),  # Path to left logo in static folder
        'right_logo_url': static('main/bagong-pilipinas-logo.png'),  # Path to right logo in static folder
        'is_lead_auditor': is_lead_auditor,  # Role-specific context
    }

    # Render the appropriate template based on the role
    if is_lead_auditor:
        return render(request, 'main/lead auditor/rfa_view.html', context)
    else:
        return render(request, 'main/form/rfa_view.html', context)

@login_required
def process_owner_preview_rfa(request, nc_id):
    """
    View for Process Owner to preview a Request for Action (RFA).
    """
    # Fetch the Non-Conformity object
    non_conformity = get_object_or_404(NonConformity, id=nc_id, assigned_to=request.user)

    context = {
        'non_conformity': non_conformity,
    }
    return render(request, 'main/process owner/rfa_view.html', context)

def generate_pdf(request, nc_id):
    # Fetch the NonConformity object by its ID
    non_conformity = get_object_or_404(NonConformity, id=nc_id)

    # Fetch related data
    immediate_action = ImmediateAction.objects.filter(non_conformity=non_conformity).first()
    root_cause_analysis = RootCauseAnalysis.objects.filter(non_conformity=non_conformity).first()
    corrective_action_plans = CorrectiveActionPlan.objects.filter(non_conformity=non_conformity)
    follow_up_actions = FollowUpAction.objects.filter(non_conformity=non_conformity)
    close_out = getattr(non_conformity, 'close_out', None)

    action_verifications = ActionVerification.objects.filter(
        corrective_action_plan__in=corrective_action_plans
    )

    # Prepare reviews for corrective action plans
    reviews = []
    for cap in corrective_action_plans:
        review = cap.reviews.last()  # Fetch the latest review for each CAP, if any
        reviews.append({
            'effectiveness': review.effectiveness if review else "N/A",
            'reason': review.reason if review and review.reason else "N/A",
            'reviewer': review.reviewer.get_full_name() if review and review.reviewer else "N/A",
            'review_date': review.review_date if review else "N/A"
        })

    # Handle missing or null data in root_cause_analysis
    root_cause_data = {
        'cause_description': root_cause_analysis.cause_description if root_cause_analysis and root_cause_analysis.cause_description else "N/A",
        'rca_date': root_cause_analysis.rca_date if root_cause_analysis and root_cause_analysis.rca_date else "N/A",
        'responsible_officer': root_cause_analysis.responsible_officer if root_cause_analysis and root_cause_analysis.responsible_officer else "N/A",
        'estimated_close_date': root_cause_analysis.estimated_close_date if root_cause_analysis and root_cause_analysis.estimated_close_date else "N/A",
    }
    current_site = request.build_absolute_uri('/')  # Get the current site URL
    # Prepare the context
    context = {
        'non_conformity': non_conformity,
        'immediate_action': immediate_action,
        'root_cause_analysis': root_cause_data,
        'corrective_action_plans': corrective_action_plans,
        'reviews': reviews,  # Include reviews in the context
        'follow_up_actions': follow_up_actions,
        'action_verifications': action_verifications,
        'close_out': close_out,
        'left_logo_url': static('main/iso-sorsu-logo.png'),  # Path to left logo in static folder
        'right_logo_url': static('main/bagong-pilipinas-logo.png'),  # Path to right logo in static folder
    }

    # Render the HTML template
    html = render_to_string('main/form/rfa_page1.html', context)

    # Debugging: Save the HTML to a file for inspection
    with open('debug_rendered_template.html', 'w', encoding='utf-8') as file:
        file.write(html)

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="FM-QMS-010-RFA-Form.pdf"'

    # Convert HTML to PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    # Check for errors
    if pisa_status.err:
        # Log the error to a file for debugging
        with open('pdf_error_log.txt', 'w', encoding='utf-8') as error_file:
            error_file.write(f"Error during PDF generation: {pisa_status.err}")
        return HttpResponse('An error occurred while generating the PDF', status=500)

    return response


def notifications_view(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if not authenticated

    # Fetch notifications for the logged-in user
    notifications = request.user.notifications.all().order_by('-timestamp')

    return render(request, 'main/internal audit/notifications.html', {'notifications': notifications})


def mark_all_notifications_read(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if not authenticated

    # Mark all unread notifications as read
    request.user.notifications.mark_all_as_read()

    return redirect('notifications')  # Redirect back to the notifications page


def mark_notification_as_read(request, notification_id):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if not authenticated

    # Fetch the specific notification
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()

    return redirect('notifications')  # Redirect back to the notifications page


def internal_audit_view(request):
    # Fetch all non-conformities
    non_conformities = NonConformity.objects.all()

    # Compute counts for each tab dynamically
    ongoing_count = non_conformities.filter(status='pending').count()
    finished_count = non_conformities.filter(status='corrective_action_completed').count()
    postponed_count = non_conformities.filter(status='postponed').count()

    context = {
        'non_conformities': non_conformities,
        'ongoing_count': ongoing_count,
        'finished_count': finished_count,
        'postponed_count': postponed_count,
    }
    return render(request, 'main/internal audit/internal_auditor_monitoring_log.html', context)


def is_lead_auditor(user):
    return hasattr(user, 'userprofile') and user.userprofile.role == 'Lead Auditor'


logger = logging.getLogger(__name__)

@login_required
@user_passes_test(is_lead_auditor)
def lead_auditor_monitoring_log(request):
    """
    View for Lead Auditor Monitoring Log. Display all non-conformities and their status.
    Automatically update status based on corrective action status.
    """
    # Fetch all non-conformities
    non_conformities = NonConformity.objects.all()

    # Automate status updates based on corrective action plans and verifications
    for nc in non_conformities:
        if nc.status == 'open' and nc.corrective_action_plans.exists():
            # Update to 'pending' if a corrective action plan exists
            nc.status = 'pending'
            nc.save()

        elif nc.status == 'pending' and nc.corrective_action_plans.filter(action_verifications__status='effective').exists():
            # Update to 'closed' if corrective action plan has been verified as effective
            nc.status = 'closed'
            nc.save()

    # Compute counts for each status
    ongoing_count = non_conformities.filter(status='in_progress').count()
    finished_count = non_conformities.filter(status='completed').count()
    postponed_count = non_conformities.filter(status='postponed').count()
    open_count = non_conformities.filter(status='open').count()
    pending_count = non_conformities.filter(status='pending').count()  # Add pending count
    closed_count = non_conformities.filter(status='closed').count()  # Add closed count

    context = {
        'non_conformities': non_conformities,
        'ongoing_count': ongoing_count,
        'finished_count': finished_count,
        'postponed_count': postponed_count,
        'open_count': open_count,  # Add open count to context
        'pending_count': pending_count,  # Add pending count to context
        'closed_count': closed_count,  # Add closed count to context
    }

    return render(request, 'main/lead auditor/lead_auditor_monitoring_log.html', context)





def lead_auditor_manage_user(request):
    # Example messages
    for message in messages.get_messages(request):
        message.icon = 'success' if 'success' in message.tags else 'error'

    users = User.objects.all()
    user_profiles = UserProfile.objects.select_related('user').all()
    user_roles = {profile.user.id: profile.get_role_display() for profile in user_profiles}

    context = {
        'users': users,
        'user_roles': user_roles,
    }
    return render(request, 'main/lead auditor/lead_auditor_manage_user.html', context)


@login_required
def user_profile_view(request):
    # Handle GET request to fetch user profile data
    if request.method == "GET":
        profile = get_object_or_404(UserProfile, user=request.user)
        data = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "phone_number": profile.phone_number,
            "position": profile.position,
            "department": profile.department,
            "role": profile.role,
        }
        return JsonResponse(data)

    # Handle POST request to update user profile data
    elif request.method == "POST":
        try:
            profile = get_object_or_404(UserProfile, user=request.user)
            data = request.POST

            # Update user fields
            request.user.first_name = data.get("firstName", request.user.first_name)
            request.user.last_name = data.get("lastName", request.user.last_name)
            request.user.email = data.get("email", request.user.email)
            request.user.save()

            # Update profile fields
            profile.phone_number = data.get("phone", profile.phone_number)
            profile.position = data.get("position", profile.position)
            profile.department = data.get("department", profile.department)
            profile.save()

            return JsonResponse({"message": "Profile updated successfully!"})
        except Exception as e:
            return JsonResponse({"message": "Error updating profile", "error": str(e)}, status=500)

    # Return an error if request method is not GET or POST
    return JsonResponse({"message": "Invalid request method"}, status=400)


# View for creating an announcement
# View for displaying all announcements
def view_announcements(request):
    announcements = Announcement.objects.all()
    return render(request, 'main/lead auditor/announcements/view_announcement.html', {'announcements': announcements})


# View for creating a new announcement
# Create Announcement
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            return redirect('view_announcements')
    return redirect('view_announcements')  # Handle invalid cases


# View for editing an existing announcement
def update_announcement(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            return redirect('view_announcements')
    return redirect('view_announcements')


# Delete Announcement
def delete_announcement(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    if request.method == 'POST':
        announcement.delete()
        return redirect('view_announcements')
    return redirect('view_announcements')


def audit_report_summary_view(request, audit_details_id):
    # Fetch the specific AuditDetails instance
    audit_details = get_object_or_404(AuditDetails, id=audit_details_id)

    # Fetch GoodPoints linked to this AuditDetails
    good_points = GoodPoints.objects.filter(audit_detail=audit_details)

    non_conformities = NonConformity.objects.filter(status='completed')  # Adjust as needed
    for nc in non_conformities:
        if not AuditFinding.objects.filter(linked_rfa=nc).exists():  # Ensure the AuditFinding doesn't already exist
            AuditFinding.create_from_non_conformity(nc)  # Create AuditFinding from NonConformity

    # Fetch all audit findings to display
    audit_findings = AuditFinding.objects.all()

    audit_finding_form = AuditFindingForm(request.POST or None)

    campus_name = good_points.first().campus if good_points.exists() else "Unknown Campus"

    # Debugging outputs
    print("Audit Details:", audit_details)
    print("Good Points:", list(good_points))
    print("Audit Findings:", list(audit_findings))

    # Context for rendering the template
    context = {
        'audit_details': audit_details,
        'good_points': good_points,
        'audit_findings': audit_findings,
        'audit_finding_form': audit_finding_form,
        'campus_name': campus_name,
    }

    return render(request, 'main/lead auditor/audit_report.html', context)


def generate_audit_report_summary_pdf(request, date_range):
    # Fetch the audit details for the given date range
    audit_details = AuditDetails.objects.filter(date_range=date_range).first()
    if not audit_details:
        return HttpResponse('No audit details found for the given date range.', status=404)

    # Fetch associated GoodPoints
    good_points = GoodPoints.objects.filter(audit_detail=audit_details)

    # Fetch related NonConformities linked by location
    non_conformities = NonConformity.objects.filter(unit_department=audit_details.location)

    # Fetch AuditFindings
    audit_findings = AuditFinding.objects.all()

    campus_name = good_points.first().campus if good_points.exists() else "Unknown Campus"

    # Prepare context for PDF rendering
    context = {
        'audit_details': audit_details,
        'good_points': good_points,
        'non_conformities': non_conformities,
        'audit_findings': audit_findings,
        'left_logo_url': request.build_absolute_uri(static('main/iso-sorsu-logo.png')),
        'right_logo_url': request.build_absolute_uri(static('main/bagong-pilipinas-logo.png')),
        'campus_name': campus_name,
    }

    # Render the HTML template to a string
    html = render_to_string('main/lead auditor/audit_report_summary.html', context)

    # Create the PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Audit_Report_Summary_{date_range}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    # Handle errors
    if pisa_status.err:
        return HttpResponse('An error occurred while generating the PDF.', status=500)

    return response


def save_audit_details(request):
    if request.method == 'POST':
        # Get the submitted data
        date_range = request.POST.get('date_range')
        location = request.POST.get('location')

        # Check if a similar AuditDetails already exists
        audit_details, created = AuditDetails.objects.get_or_create(
            date_range=date_range,
            location=location
        )

        # Save Good Points linked to this AuditDetails
        good_points = request.POST.getlist('good_points[]')
        for point in good_points:
            if point.strip():  # Avoid saving empty points
                GoodPoints.objects.create(
                    audit_detail=audit_details,
                    description=point.strip(),
                    campus=location  # Example association
                )

        # Redirect to the summary view with the correct audit_details_id
        return redirect('audit_report_summary', audit_details_id=audit_details.id)
