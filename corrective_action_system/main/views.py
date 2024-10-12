from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from itsdangerous import URLSafeTimedSerializer
from django.contrib.auth.models import User
from django.contrib import messages
from .models import LoginEvent, UserProfile
from .forms import UserCreationForm, UserUpdateForm
from django.http import HttpResponse, FileResponse, Http404
from .models import TemplateModel, Guideline, Announcement
from .forms import GuidelineForm, AnnouncementForm, CustomPasswordChangeForm
from itsdangerous import SignatureExpired, BadSignature
from django.http import JsonResponse
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
    return render(request, 'main/process owner/process_owner_dashboard.html')


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
    return hasattr(user, 'userprofile') and user.userprofile.role in ['Admin', 'Internal Auditor']


@login_required
@user_passes_test(role_allowed_to_delete)
def delete_template(request, pk):
    template = get_object_or_404(TemplateModel, pk=pk)
    if template.file:
        template.file.delete(save=False)
    template.delete()

    # Redirect based on user role
    if request.user.userprofile.role == 'Admin':
        return redirect('forms')
    elif request.user.userprofile.role == 'Internal Auditor':
        return redirect('internal_auditor_forms')
    else:
        # Default redirection if none of the roles match
        return redirect('forms')


@login_required
def internal_auditor_forms_view(request):
    templates = TemplateModel.objects.all()
    return render(request, 'main/internal audit/internal_auditor_forms.html', {'templates': templates})


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

def admin_upload_guideline(request):
    if request.method == "POST":
        form = GuidelineForm(request.POST, request.FILES)
        if form.is_valid():
            guideline = form.save(commit=False)
            guideline.uploaded_by = request.user
            guideline.save()
            messages.success(request, "Guideline uploaded successfully.")
            return redirect('admin_guideline_list')
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


@login_required
def add_project(request):
    if request.method == "POST":
        non_conformity = request.POST.get('non_conformity')
        assignees = request.POST.get('assignees')
        campus = request.POST.get('campus')
        start_date = request.POST.get('start_date')
        deadline = request.POST.get('deadline')
        task = request.POST.get('task')

        # Add logic for saving the project

        messages.success(request, 'Project added successfully.')
        return redirect('internal_auditor_monitoring_log')  # Redirect after adding project

    # If not POST request, render the form to add a project
    return render(request, 'main/internal audit/internal_auditor_add_new_nc.html')


