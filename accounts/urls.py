from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('signup/',views.signup, name='signup'),
    path('login/',views.user_login, name='login'),
    path('logout/',views.logout_view, name='logout'),
    path('dashboard/',views.dashboard, name='dashboard'),
    path('teacher_dashboard/',views.teacher_dashboard, name='teacher_dashboard'),
    path('exam/<int:course_id>/',views.take_exam, name='take_exam'),
    path('edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('exam/<int:course_id>/questions/', views.course_questions, name='course_questions'),
    path('edit-question/<int:question_id>/', views.edit_question, name='edit_question'),
    path('delete-question/<int:question_id>/', views.delete_question, name='delete_question'),
    path('add-course/', views.add_course, name='add_course'),
    path('add-question/<int:course_id>/', views.add_question, name='add_question'),
    path('export-results/', views.export_results_csv, name='export_results_csv'),

]