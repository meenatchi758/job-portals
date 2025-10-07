from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, Job, JobApplication, Interview, JobCategory  # Add JobCategory here

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPES)
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    company_name = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            user_profile = UserProfile.objects.create(
                user=user,
                user_type=self.cleaned_data['user_type'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                company_name=self.cleaned_data['company_name']
            )
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'company_name', 'resume', 'profile_picture']

class JobForm(forms.ModelForm):
    application_deadline = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Select the last date for applications"
    )
    
    salary = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50000.00'}),
        help_text="Optional: Enter annual salary"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ensure category field has proper queryset
        self.fields['category'].queryset = JobCategory.objects.all()
        self.fields['category'].empty_label = "Select a category"
        self.fields['category'].widget.attrs.update({'class': 'form-control'})
        
        # Set up all fields with proper attributes
        self.fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter job title...'
        })
        
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe the job responsibilities, role, etc...'
        })
        
        self.fields['job_type'].widget.attrs.update({'class': 'form-control'})
        
        self.fields['location'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'e.g., New York, NY or Remote'
        })
        
        self.fields['requirements'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'List the requirements for this position...'
        })
        
        self.fields['skills_required'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'List required skills separated by commas...'
        })

    class Meta:
        model = Job
        fields = ['title', 'description', 'category', 'job_type', 'location', 
                 'salary', 'requirements', 'skills_required', 'application_deadline']
        
    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')
        if deadline and deadline < timezone.now().date():
            raise forms.ValidationError("Application deadline cannot be in the past.")
        return deadline

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your cover letter here...'}),
        }

class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['scheduled_date', 'duration', 'interview_type', 'location_or_link', 'notes']
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }