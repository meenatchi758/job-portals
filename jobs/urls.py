from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='jobs/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    path('profile/', views.profile, name='profile'),
    path('jobs/', views.job_list, name='job_list'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('employer/post-job/', views.post_job, name='post_job'),
    path('employer/application/<int:application_id>/update-status/', 
         views.update_application_status, name='update_application_status'),
    path('employer/application/<int:application_id>/schedule-interview/', 
         views.schedule_interview, name='schedule_interview'),
    path('employer/application/<int:application_id>/view-resume/', 
         views.view_resume, name='view_resume'),
    path('employer/application/<int:application_id>/download-resume/', 
         views.download_resume, name='download_resume'),
    
    path('job-seeker/dashboard/', views.job_seeker_dashboard, name='job_seeker_dashboard'),
]