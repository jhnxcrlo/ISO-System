from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from itsdangerous import URLSafeTimedSerializer
from django.contrib.auth.models import User
from django.contrib import messages
from .models import LoginEvent, UserProfile, ImmediateAction, RootCauseAnalysis, CorrectiveActionPlan
from .forms import UserCreationForm, UserUpdateForm, RootCauseAnalysisForm, ImmediateActionForm, \
    CorrectiveActionPlanForm
from django.http import HttpResponse, FileResponse, Http404
from .models import TemplateModel, Guideline, Announcement, NonConformity
from .forms import GuidelineForm, AnnouncementForm, CustomPasswordChangeForm
from itsdangerous import SignatureExpired, BadSignature
from django.contrib.auth import update_session_auth_hash
import logging

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
            else:
                return redirect('dashboard')
        else:
            return render(request, 'main/login.html', {'error': 'Invalid username or password'})
    return render(request, 'main/login.html')


@login_required
def dashboard_view(request):
    return render(request, 'main/administrator/dashboard.html')


@login_required
def internal_auditor_dashboard_view(request):
    return render(request, 'main/internal audit/internal_auditor_dashboard.html')


@login_required
def process_owner_dashboard_view(request):
    tasks = NonConformity.objects.filter(assigned_to=request.user, status='pending')
    return render(request, 'main/process owner/process_owner_dashboard.html', {'tasks': tasks})


logger = logging.getLogger(__name__)


@login_required
def manage_users_view(request):
    # Get all users and their profiles with role information
    users = User.objects.all()
    user_profiles = UserProfile.objects.select_related('user').all()

    # Create a dictionary of user IDs and roles for easy access in the template
    user_roles = {profile.user.id: profile.get_role_display() for profile in user_profiles}

    # Create an empty form for adding users
    add_user_form = UserCreationForm()

    # Context to pass to the template
    context = {
        'users': users,  # List of users to display
        'user_roles': user_roles,  # Dictionary of user roles by user ID
        'add_user_form': add_user_form,  # Empty form for adding users
    }

    return render(request, 'main/administrator/manage_users.html', context)


@login_required
def add_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')  # Get user_id if it's an edit
        logger.info(f'Handling user creation/edit. User ID: {user_id}')

        if user_id:
            # If user_id exists, it's an update, fetch the user and update their info
            user = get_object_or_404(User, id=user_id)
            form = UserUpdateForm(request.POST, instance=user)
        else:
            # If no user_id, it's a new user creation
            form = UserCreationForm(request.POST)

        if form.is_valid():
            # If the form is valid, save the user
            if user_id:
                # Update existing user
                form.save()
                messages.success(request, 'User account has been successfully updated.')
                logger.info(f'User {user.username} updated successfully.')
            else:
                # Create a new user and set a default password
                user = form.save(commit=False)  # Save user data but don't commit to DB yet
                default_password = 'sorsu123'  # Set your default password here
                user.set_password(default_password)
                user.save()  # Save the user to the database
                logger.info(f'New user {user.username} created with default password.')

                # Create a user profile and set role
                UserProfile.objects.create(user=user, role=form.cleaned_data['role'])

                # Force the user to change their password on first login
                user.userprofile.password_needs_reset = True
                user.userprofile.save()

                # Send email for account creation and verification (if email verification is required)
                token = s.dumps(user.email, salt='email-confirm')
                verification_link = request.build_absolute_uri(f'/main/verify/{token}/')

                subject = 'Account Created - Verify your email address'
                html_content = render_to_string('main/administrator/confirmation_email.html',
                                                {'verification_link': verification_link})
                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(subject, text_content, 'jhnxcrlo@gmail.com', [user.email])
                email.attach_alternative(html_content, "text/html")
                email.send()

                messages.success(request, 'User account has been successfully created.')
                logger.info(f'User {user.username} email sent with verification link.')

            # After successful creation or update, redirect to the manage users page
            return redirect('manage_users')
        else:
            # If the form is invalid, log errors and re-render the page with error messages
            logger.error(f'Form validation failed. Errors: {form.errors}')
            messages.error(request, 'Please correct the errors below.')

            # Re-display the manage users page with the form containing validation errors
            users = User.objects.all()
            user_profiles = UserProfile.objects.select_related('user').all()
            user_roles = {profile.user.id: profile.get_role_display() for profile in user_profiles}
            context = {
                'users': users,
                'user_roles': user_roles,
                'add_user_form': form,  # Return the form with errors
            }
            return render(request, 'main/administrator/manage_users.html', context)

    return redirect('manage_users')


@login_required
def delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Check if the request is POST and the user has permission to delete
    if request.method == 'POST':
        if request.user.is_superuser or request.user == user:
            # Delete the user and show a success message
            user.delete()
            messages.success(request, 'User account has been successfully deleted.')
            logger.info(f'User {user.username} deleted.')
            return redirect('manage_users')
        else:
            return HttpResponse('Unauthorized', status=403)

    # If it's not a POST request, render the confirmation page
    return render(request, 'main/administrator/confirm_delete.html', {'user': user})


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
                return redirect('process_owner_dashboard')  # Ensure this URL name is defined
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

    return render(request, 'main/administrator/change_password.html', {'form': form})


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


def announcement_list(request):
    announcements = Announcement.objects.all()
    form = AnnouncementForm()
    return render(request, 'main/administrator/announcements/announcement_list.html',
                  {'announcements': announcements, 'form': form})


@login_required
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user  # Set the creator
            announcement.save()
            return redirect('announcement_list')
    else:
        form = AnnouncementForm()

    return render(request, 'main/administrator/announcements/announcement_list.html', {'form': form})


@login_required
def update_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            return redirect('announcement_list')


@login_required
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        announcement.delete()
        return redirect('announcement_list')


@login_required
def forms_view(request):
    templates = TemplateModel.objects.all()
    return render(request, 'main/administrator/forms.html', {'templates': templates})


@login_required
def upload_template(request):
    if request.method == 'POST':
        template_name = request.POST.get('template_name')
        template_description = request.POST.get('template_description')
        template_file = request.FILES.get('template_file')

        if template_file:
            template_model = TemplateModel.objects.create(
                template_name=template_name,
                description=template_description,
                file=template_file
            )
            template_model.save()
            return redirect('forms')

        return render(request, 'main/administrator/forms.html', {'error': 'No file was uploaded.'})

    return redirect('forms')


@login_required
def download_template(request, pk):
    template = get_object_or_404(TemplateModel, pk=pk)
    if template.file:
        try:

            file = template.file.open('rb')
            response = FileResponse(file, as_attachment=True, filename=template.file.name)
            return response
        except FileNotFoundError:
            raise Http404("File not found.")
    return redirect('forms')



def role_allowed_to_delete(user):
    print(f"User {user.username} with role {user.userprofile.role} is trying to delete.")
    return hasattr(user, 'userprofile') and user.userprofile.role in ['Admin', 'Internal Auditor']


@login_required
@user_passes_test(role_allowed_to_delete)
def delete_template(request, pk):
    template = get_object_or_404(TemplateModel, pk=pk)
    if request.method == "POST":
        if template.file:
            template.file.delete(save=False)
        template.delete()

        messages.success(request, "Template deleted successfully.")

    # Redirect to appropriate page based on the user's role
    if request.user.userprofile.role == 'Admin':
        return redirect('forms')
    elif request.user.userprofile.role == 'Internal Auditor':
        return redirect('internal_auditor_forms')
    else:
        return redirect('forms')


@login_required
def internal_auditor_forms_view(request):
    templates = TemplateModel.objects.all()
    return render(request, 'main/internal audit/internal_auditor_forms.html', {'templates': templates})

@login_required
def internal_upload_template(request):
    if request.method == 'POST':
        template_name = request.POST.get('template_name')
        template_description = request.POST.get('template_description')
        template_file = request.FILES.get('template_file')

        if template_file:
            template_model = TemplateModel.objects.create(
                template_name=template_name,
                description=template_description,
                file=template_file
            )
            template_model.save()
            return redirect('forms')

        return render(request, 'main/administrator/forms.html', {'error': 'No file was uploaded.'})

    return redirect('forms')


@login_required
def process_owner_forms_view(request):
    templates = TemplateModel.objects.all()  # List all available forms
    return render(request, 'main/process owner/process_owner_forms.html', {'templates': templates})



@login_required
def internal_auditor_monitoring_log(request):
    # Your logic here
    return render(request, 'main/internal audit/internal_auditor_monitoring_log.html')


@login_required
def admin_guideline_list(request):
    guidelines = Guideline.objects.all()
    for guideline in guidelines:
        logger.info(f"File URL: {guideline.file.url}")
    return render(request, 'main/administrator/guidelines/list.html', {'guidelines': guidelines})


@login_required

@login_required
def admin_upload_guideline(request):
    if request.method == "POST":
        form = GuidelineForm(request.POST, request.FILES)
        if form.is_valid():
            guideline = form.save(commit=False)
            guideline.uploaded_by = request.user
            guideline.save()
            messages.success(request, "Guideline uploaded successfully.")
            return redirect('admin_guideline_list')  # Redirect to Guidelines
        else:
            messages.error(request, "Failed to upload guideline. Please check the form.")
    else:
        form = GuidelineForm()

    return render(request, 'main/administrator/guidelines/upload.html', {'form': form})


@login_required

def admin_edit_guideline(request, pk):
    guideline = get_object_or_404(Guideline, pk=pk)
    if request.method == "POST":
        form = GuidelineForm(request.POST, request.FILES, instance=guideline)
        if form.is_valid():
            form.save()
            messages.success(request, "Guideline updated successfully.")
            return redirect('admin_guideline_list')
        else:
            messages.error(request, "Failed to update guideline. Please check the form.")
    else:
        form = GuidelineForm(instance=guideline)

    return render(request, 'main/administrator/guidelines/edit.html', {'form': form, 'guideline': guideline})


@login_required
def admin_delete_guideline(request, pk):
    guideline = get_object_or_404(Guideline, pk=pk)
    if request.method == "POST":
        guideline.delete()
        messages.success(request, "Guideline deleted successfully.")
        return redirect('admin_guideline_list')

    return render(request, 'main/administrator/guidelines/delete_confirm.html', {'guideline': guideline})


# Check if user is internal auditor
def is_internal_auditor(user):
    return hasattr(user, 'userprofile') and user.userprofile.role == 'Internal Auditor'


@login_required
@user_passes_test(is_internal_auditor)
def internal_auditor_guideline_list(request):
    guidelines = Guideline.objects.all()
    return render(request, 'main/internal audit/list.html', {'guidelines': guidelines})


@login_required
@user_passes_test(is_internal_auditor)
def internal_auditor_upload_guideline(request):
    if request.method == "POST":
        form = GuidelineForm(request.POST, request.FILES)
        if form.is_valid():
            guideline = form.save(commit=False)
            guideline.uploaded_by = request.user
            guideline.save()
            messages.success(request, "Guideline uploaded successfully.")
            return redirect('internal_auditor_guideline_list')
        else:
            messages.error(request, "Failed to upload guideline. Please check the form.")
    else:
        form = GuidelineForm()

    return render(request, 'main/internal audit/upload_guideline.html', {'form': form})


@login_required
@user_passes_test(is_internal_auditor)
def internal_auditor_edit_guideline(request, pk):
    guideline = get_object_or_404(Guideline, pk=pk)
    if request.method == "POST":
        form = GuidelineForm(request.POST, request.FILES, instance=guideline)
        if form.is_valid():
            form.save()
            messages.success(request, "Guideline updated successfully.")
            return redirect('internal_auditor_guideline_list')
        else:
            messages.error(request, "Failed to update guideline. Please check the form.")
    else:
        form = GuidelineForm(instance=guideline)

    return render(request, 'main/internal audit/edit_guideline.html', {'form': form, 'guideline': guideline})


@login_required
@user_passes_test(is_internal_auditor)
def internal_auditor_delete_guideline(request, pk):
    guideline = get_object_or_404(Guideline, pk=pk)
    if request.method == "POST":
        guideline.delete()
        messages.success(request, "Guideline deleted successfully.")
        return redirect('internal_auditor_guideline_list')

    return render(request, 'main/internal audit/delete_guideline.html', {'guideline': guideline})


# Check if user is process owner
def is_process_owner(user):
    return hasattr(user, 'userprofile') and user.userprofile.role == 'Process Owner'


@login_required
@user_passes_test(is_process_owner)
def process_owner_guideline_list(request):
    guidelines = Guideline.objects.all()
    return render(request, 'main/process owner/list.html', {'guidelines': guidelines})


def add_non_conformity(request):
    if request.method == 'POST':
        # Get form data
        non_conformity = request.POST.get('non_conformity')
        assignees = request.POST.get('assignees')
        originator_name = request.POST.get('originator_name')
        unit_department = request.POST.get('unit_department')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        rfa_intent = request.POST.get('rfa_intent')
        department = request.POST.get('department')
        non_conformance_category = request.POST.get('non_conformance_category')
        description_of_non_conformance = request.POST.get('description_of_non_conformance')
        iso_clause = request.POST.get('iso_clause')
        category = request.POST.get('category')
        task = request.POST.get('task')
        start_date = request.POST.get('start_date')
        deadline = request.POST.get('deadline')
        assigned_to_id = request.POST.get('assigned_to')

        # Get the assigned process owner
        assigned_to = User.objects.get(id=assigned_to_id)

        # Create NonConformity instance
        NonConformity.objects.create(
            non_conformity=non_conformity,
            assignees=assignees,
            originator_name=originator_name,
            unit_department=unit_department,
            phone=phone,
            email=email,
            rfa_intent=rfa_intent,
            department=department,
            non_conformance_category=non_conformance_category,
            description_of_non_conformance=description_of_non_conformance,
            iso_clause=iso_clause,
            category=category,
            task=task,
            start_date=start_date,
            deadline=deadline,
            assigned_to=assigned_to,  # Assign to selected process owner
            status='pending'
        )

        return redirect('internal_auditor_monitoring_log')  # Redirect to the process owner's dashboard

    # Fetch all process owners for dropdown
    process_owners = User.objects.filter(userprofile__role='Process Owner')
    return render(request, 'main/internal audit/add_non_conformity.html', {
        'process_owners': process_owners
    })

def fm_qms_010_page_1(request):
    return render(request, 'main/internal audit/fm_qms_010_page_1.html')


def task_detail(request, task_id):
    task = get_object_or_404(NonConformity, id=task_id)

    # Check if ImmediateAction already exists
    immediate_action = ImmediateAction.objects.filter(non_conformity=task).first()
    root_cause_analysis = RootCauseAnalysis.objects.filter(non_conformity=task).first()

    context = {
        'task': task,
        'immediate_action': immediate_action,
        'root_cause_analysis': root_cause_analysis,
    }

    if immediate_action:
        # Show only Root Cause Analysis form if Immediate Action exists
        context['form'] = RootCauseAnalysisForm(instance=root_cause_analysis)
        context['form_action_url'] = 'add_root_cause_analysis'
    else:
        # Show Immediate Action form if it doesn't exist
        context['form'] = ImmediateActionForm(instance=immediate_action)
        context['form_action_url'] = 'add_immediate_action'

    return render(request, 'main/process owner/task_detail.html', context)

# View for saving Immediate Action
def add_immediate_action(request, task_id):
    task = get_object_or_404(NonConformity, id=task_id)

    if request.method == 'POST':
        # Retrieve or create the related ImmediateAction instance
        immediate_action, created = ImmediateAction.objects.get_or_create(non_conformity=task)

        # Update the action description with the posted data
        immediate_action.action_description = request.POST.get('immediate_action')
        immediate_action.save()  # Save the ImmediateAction instance

        return redirect('task_detail', task_id=task.id)

    # If GET request, load the page (not typically needed for this form processing view)
    return redirect('task_detail', task_id=task.id)

# View for saving Root Cause Analysis
def add_root_cause_analysis(request, task_id):
    # Retrieve the associated NonConformity instance
    task = get_object_or_404(NonConformity, id=task_id)

    if request.method == 'POST':
        # Get or create the related RootCauseAnalysis instance
        root_cause_analysis, created = RootCauseAnalysis.objects.get_or_create(non_conformity=task)

        # Update fields with POST data
        root_cause_analysis.cause_description = request.POST.get('root_cause', '')
        root_cause_analysis.rca_date = request.POST.get('rca_date')
        root_cause_analysis.responsible_officer = request.POST.get('responsible_officer', '')
        root_cause_analysis.estimated_close_date = request.POST.get('estimated_close_date')

        # Validate mandatory fields
        if not root_cause_analysis.cause_description or not root_cause_analysis.rca_date:
            messages.error(request, "Root cause description and date are required.")
            return redirect('task_detail', task_id=task.id)

        # Process '5 Whys' data
        five_whys_data = {f'why{i}': request.POST.get(f'five_whys[why{i}]', '') for i in range(1, 6)}
        root_cause_analysis.five_whys = five_whys_data  # Ensure field is JSONField

        # Mark the root cause analysis as completed
        root_cause_analysis.root_cause_completed = True

        # Save the instance
        root_cause_analysis.save()

        # Notify the user of success
        messages.success(request, "Root cause analysis submitted successfully.")

        # Redirect to the task detail page
        return redirect('task_detail', task_id=task.id)

    # Redirect for non-POST requests (optional)
    return redirect('task_detail', task_id=task.id)


def corrective_action_plan(request, task_id):
    task = get_object_or_404(NonConformity, id=task_id)

    if request.method == 'POST':
        # Delete existing plans to replace with new ones
        CorrectiveActionPlan.objects.filter(non_conformity=task).delete()

        # Process each row of the corrective action plan form
        row_count = len([key for key in request.POST.keys() if key.startswith('activity_')])
        for i in range(1, row_count + 1):
            activity = request.POST.get(f'activity_{i}')
            responsible_person = request.POST.get(f'responsible_person_{i}')
            time_frame = request.POST.get(f'time_frame_{i}')
            resources_needed = request.POST.get(f'resources_needed_{i}')
            result = request.POST.get(f'result_{i}', '')

            # Only save rows with required fields filled
            if activity and responsible_person and time_frame and resources_needed:
                CorrectiveActionPlan.objects.create(
                    non_conformity=task,
                    activity=activity,
                    responsible_person=responsible_person,
                    time_frame=time_frame,
                    resources_needed=resources_needed,
                    result=result
                )

        return redirect('task_detail', task_id=task.id)

    # Prepopulate existing corrective action plans for display in the template
    corrective_action_plans = CorrectiveActionPlan.objects.filter(non_conformity=task)
    context = {
        'task': task,
        'corrective_action_plans': corrective_action_plans,
    }
    return render(request, 'main/process owner/task_detail.html', context)


def rfa_create(request):
    return None