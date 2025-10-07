from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    USER_TYPES = (
        ('job_seeker', 'Job Seeker'),
        ('employer', 'Employer'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    company_name = models.CharField(max_length=100, blank=True)  # For employers
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)  # For job seekers
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class JobCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    location = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    employer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'userprofile__user_type': 'employer'})
    requirements = models.TextField()
    skills_required = models.TextField()
    posted_date = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    def is_deadline_passed(self):
        return timezone.now().date() > self.application_deadline

class JobApplication(models.Model):
    APPLICATION_STATUS = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('hired', 'Hired'),
    )
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'userprofile__user_type': 'job_seeker'})
    applied_date = models.DateTimeField(auto_now_add=True)
    cover_letter = models.TextField()
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='applied')
    
    class Meta:
        unique_together = ['job', 'applicant']
    
    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"

class Interview(models.Model):
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE)
    scheduled_date = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")  # Duration in minutes
    interview_type = models.CharField(max_length=50, choices=[
        ('in_person', 'In Person'),
        ('phone', 'Phone'),
        ('video', 'Video Call'),
    ])
    location_or_link = models.TextField(help_text="Physical address or video call link")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Interview for {self.application.job.title}"