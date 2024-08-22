from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from itsdangerous import URLSafeTimedSerializer
from django.contrib.auth.models import User
from django.contrib import messages
from .models import LoginEvent, UserProfile
from .forms import UserCreationForm, UserUpdateForm
from django.http import HttpResponse, FileResponse, Http404
from .models import Announcement, TemplateModel
from .forms import AnnouncementForm
from .forms import ReportForm, TemplateForm
from django.core.files.storage import default_storage
from urllib.parse import quote

s = URLSafeTimedSerializer('your-secret-key')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            # Log the login event and update user profile with the selected role
            LoginEvent.objects.create(user=user)
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            request.session['user_role'] = user_profile.role  # Save the role in the session

            # Redirect based on user role
            if user_profile.role == 'Internal Auditor':
                return redirect('main:internal_auditor_dashboard')
            elif user_profile.role == 'Process Owner':
                return redirect('main:process_owner_dashboard')
            else:
                return redirect('main:dashboard')  # Default redirect
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


@login_required
def manage_users_view(request):
    users = User.objects.all()
    user_profiles = UserProfile.objects.select_related('user').all()

    user_roles = {profile.user.id: profile.get_role_display() for profile in user_profiles}
    superuser = User.objects.filter(is_superuser=True).first()
    superuser_id = superuser.id if superuser else None
    add_user_form = UserCreationForm()

    context = {
        'users': users,
        'user_roles': user_roles,
        'superuser_id': superuser_id,
        'user_role': user_profiles.get(user=request.user).get_role_display() if request.user.is_authenticated else 'Unknown Role',
        'add_user_form': add_user_form,
    }

    return render(request, 'main/administrator/manage_users.html', context)


def add_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:  # Edit user
            user = get_object_or_404(User, id=user_id)
            form = UserUpdateForm(request.POST, instance=user)
        else:  # Add new user
            form = UserCreationForm(request.POST)

        if form.is_valid():
            if user_id:
                form.save()
                messages.success(request, 'User account has been successfully updated.')
            else:
                user = form.save()
                UserProfile.objects.create(user=user, role=form.cleaned_data['role'])
                messages.success(request, 'User account has been successfully created.')

                token = s.dumps(user.email, salt='email-confirm')
                verification_link = request.build_absolute_uri(f'/main/verify/{token}/')

                # Send confirmation email
                subject = 'Account Created - Verify your email address'
                html_content = render_to_string('main/administrator/confirmation_email.html',
                                                {'verification_link': verification_link})
                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(subject, text_content, 'jhnxcrlo@gmail.com', [user.email])
                email.attach_alternative(html_content, "text/html")
                email.send()

            return redirect('main:manage_users')
        else:
            messages.error(request, 'Please correct the errors below.')
            return redirect('main:manage_users')

    return redirect('main:manage_users')


@login_required
def delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if request.user.is_superuser or request.user == user:
            user.delete()
            messages.success(request, 'User account has been successfully deleted.')
            return redirect('main:manage_users')
        else:
            return HttpResponse('Unauthorized', status=403)

    return render(request, 'main/administrator/confirm_delete.html', {'user': user})


def verify_email(request, token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        user = User.objects.get(email=email)
        user_profile = UserProfile.objects.get(user=user)
        user_profile.email_verified = True
        user_profile.save()
        messages.success(request, 'Email successfully verified.')
        return redirect('main:login')  # Ensure this URL name matches your login view's URL pattern
    except Exception as e:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('main:login')  # Ensure this URL name matches your login view's URL pattern


def announcement_list(request):
    announcements = Announcement.objects.all()
    return render(request, 'main/administrator/announcement_list.html', {'announcements': announcements})


def announcement_create(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement created successfully!")
            return redirect('main:announcement_list')
    else:
        form = AnnouncementForm()
    return render(request, 'announcements/announcement_form.html', {'form': form})


def announcement_update(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement updated successfully!")
            return redirect('main:announcement_list')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'announcements/announcement_form.html', {'form': form})


def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        announcement.delete()
        messages.success(request, "Announcement deleted successfully!")
        return redirect('main:announcement_list')
    return render(request, 'announcements/announcement_confirm_delete.html', {'announcement': announcement})


@login_required
def guidelines_view(request):
    return render(request, 'main/administrator/guidelines.html')


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
            # Save the file using Django's default storage system
            template_model = TemplateModel.objects.create(
                template_name=template_name,
                description=template_description,
                file=template_file
            )
            template_model.save()
            return redirect('main:forms')

        return render(request, 'main/administrator/forms.html', {'error': 'No file was uploaded.'})

    return redirect('main:forms')


@login_required
def download_template(request, pk):
    template = get_object_or_404(TemplateModel, pk=pk)
    if template.file:
        try:
            # Open the file as a binary stream
            file = template.file.open('rb')
            response = FileResponse(file, as_attachment=True, filename=template.file.name)
            return response
        except FileNotFoundError:
            raise Http404("File not found.")
    return redirect('main:forms')


@login_required
def delete_template(request, pk):
    template = get_object_or_404(TemplateModel, pk=pk)
    if template.file:
        template.file.delete(save=False)  # Delete the file from the filesystem
    template.delete()  # Delete the database entry
    return redirect('main:forms')


@login_required
def generate_report(request, report_type):
    form = ReportForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Handle report generation logic here
        return render(request, 'main/report_generated.html', {'form': form, 'report_type': report_type})
    return render(request, 'main/administrator/forms.html', {'form': form, 'report_type': report_type})

