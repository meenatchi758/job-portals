from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import UserProfile, Job, JobApplication, Interview, JobCategory
from .forms import UserRegistrationForm, UserProfileForm, JobForm, JobApplicationForm, InterviewForm
from django.http import FileResponse

def home(request):
    jobs = Job.objects.filter(is_active=True).order_by('-posted_date')[:8]
    categories = JobCategory.objects.all()
    return render(request, 'jobs/home.html', {'jobs': jobs, 'categories': categories})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'jobs/register.html', {'form': form})

@login_required
def profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'jobs/profile.html', {'form': form, 'profile': user_profile})

@login_required
def post_job(request):
    # Check if user is employer and has userprofile
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, 'Please complete your profile first.')
        return redirect('profile')
    
    if request.user.userprofile.user_type != 'employer':
        messages.error(request, 'Only employers can post jobs.')
        return redirect('home')
    
    if request.method == 'POST':
        print("=== FORM SUBMISSION DETECTED ===")
        print("POST data:", request.POST)
        
        form = JobForm(request.POST)
        print("Form is bound:", form.is_bound)
        print("Form errors:", form.errors)
        print("Form is valid:", form.is_valid())
        
        if form.is_valid():
            print("Form is valid - saving job")
            job = form.save(commit=False)
            job.employer = request.user
            job.is_active = True
            print("Job object before save:", job.__dict__)
            
            try:
                job.save()
                print("Job saved successfully! ID:", job.id)
                messages.success(request, 'Job posted successfully!')
                return redirect('employer_dashboard')
            except Exception as e:
                print("Error saving job:", str(e))
                messages.error(request, f'Error saving job: {str(e)}')
        else:
            print("Form validation failed")
            print("Form errors detail:", form.errors.as_json())
            messages.error(request, 'Please correct the errors below.')
    else:
        form = JobForm()
        print("GET request - creating empty form")
    
    # Debug information
    categories = JobCategory.objects.all()
    print(f"Categories available: {categories.count()}")
    
    return render(request, 'jobs/post_job.html', {
        'form': form,
        'categories_exist': categories.exists()
    })
def job_list(request):
    # Get all active jobs with related data
    jobs = Job.objects.filter(is_active=True)\
                     .select_related('employer', 'employer__userprofile', 'category')\
                     .order_by('-posted_date')
    
    category_id = request.GET.get('category')
    job_type = request.GET.get('job_type')
    search = request.GET.get('search')
    
    # Apply filters
    if category_id:
        jobs = jobs.filter(category_id=category_id)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(skills_required__icontains=search)
        )
    
    categories = JobCategory.objects.all()
    
    # Debug output
    print("=== DEBUG JOB LIST ===")
    print(f"Total jobs in DB: {Job.objects.count()}")
    print(f"Active jobs: {jobs.count()}")
    print("Jobs found:")
    for job in jobs:
        print(f"- {job.title} (ID: {job.id}, Active: {job.is_active})")
    
    context = {
        'jobs': jobs, 
        'categories': categories,
        'selected_category': category_id,
        'selected_job_type': job_type,
        'search_query': search,
        'total_jobs': jobs.count()
    }
    
    return render(request, 'jobs/job_list.html', context)
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    has_applied = False
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'job_seeker':
            has_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()
    
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'has_applied': has_applied
    })

@login_required
def apply_job(request, job_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'job_seeker':
        messages.error(request, 'Only job seekers can apply for jobs.')
        return redirect('home')
    
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Check if already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('job_detail', job_id=job_id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, 'Application submitted successfully!')
            return redirect('job_seeker_dashboard')
    else:
        form = JobApplicationForm()
    
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})

@login_required
def job_seeker_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'job_seeker':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    applications = JobApplication.objects.filter(applicant=request.user).select_related('job')
    interviews = Interview.objects.filter(application__applicant=request.user).select_related('application__job')
    
    return render(request, 'jobs/job_seeker_dashboard.html', {
        'applications': applications,
        'interviews': interviews
    })

@login_required
def employer_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'employer':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    jobs = Job.objects.filter(employer=request.user).order_by('-posted_date')
    applications = JobApplication.objects.filter(job__employer=request.user).select_related('applicant', 'job', 'applicant__userprofile')
    
    return render(request, 'jobs/employer_dashboard.html', {
        'jobs': jobs,
        'applications': applications
    })

@login_required
def view_resume(request, application_id):
    """View job seeker's resume"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'employer':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    application = get_object_or_404(JobApplication, id=application_id, job__employer=request.user)
    
    # Check if the applicant has a resume
    if not hasattr(application.applicant, 'userprofile') or not application.applicant.userprofile.resume:
        messages.error(request, 'No resume available for this applicant.')
        return redirect('employer_dashboard')
    
    resume = application.applicant.userprofile.resume
    
    # Serve the resume file
    try:
        response = FileResponse(resume.open(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{resume.name}"'
        return response
    except Exception as e:
        messages.error(request, f'Error opening resume: {str(e)}')
        return redirect('employer_dashboard')

@login_required
def download_resume(request, application_id):
    """Download job seeker's resume"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'employer':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    application = get_object_or_404(JobApplication, id=application_id, job__employer=request.user)
    
    # Check if the applicant has a resume
    if not hasattr(application.applicant, 'userprofile') or not application.applicant.userprofile.resume:
        messages.error(request, 'No resume available for this applicant.')
        return redirect('employer_dashboard')
    
    resume = application.applicant.userprofile.resume
    
    # Serve the resume file for download
    try:
        response = FileResponse(resume.open(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{resume.name}"'
        return response
    except Exception as e:
        messages.error(request, f'Error downloading resume: {str(e)}')
        return redirect('employer_dashboard')

@login_required
def update_application_status(request, application_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'employer':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    application = get_object_or_404(JobApplication, id=application_id, job__employer=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(JobApplication.APPLICATION_STATUS):
            application.status = new_status
            application.save()
            messages.success(request, f'Application status updated to {new_status}.')
    
    return redirect('employer_dashboard')

@login_required
def schedule_interview(request, application_id):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'employer':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    application = get_object_or_404(JobApplication, id=application_id, job__employer=request.user)
    
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.application = application
            interview.save()
            
            # Update application status
            application.status = 'interview_scheduled'
            application.save()
            
            messages.success(request, 'Interview scheduled successfully!')
            return redirect('employer_dashboard')
    else:
        form = InterviewForm()
    
    return render(request, 'jobs/schedule_interview.html', {
        'form': form,
        'application': application
    })
from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')