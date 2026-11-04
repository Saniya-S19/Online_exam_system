from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('exam/<int:course_id>/', views.take_exam, name='take_exam'),
    path('edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('exam/<int:course_id>/questions/', views.course_questions, name='course_questions'),
    path('edit-question/<int:question_id>/', views.edit_question, name='edit_question'),
    path('delete-question/<int:question_id>/', views.delete_question, name='delete_question'),
    path('add-course/', views.add_course, name='add_course'),
    path('add-question/<int:course_id>/', views.add_question, name='add_question'),
    path('manage-students/<int:course_id>/', views.manage_students, name='manage_students'),
    path('export-results-csv/', views.export_results_csv, name='export_results_csv'),
    path('export-results-csv/<int:course_id>/', views.export_results_csv, name='export_results_csv_course'),
    path('api/generate-question/', views.generate_ai_question_api, name='generate_ai_question_api'),
]
