from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('signup/',views.signup, name='signup'),
    path('login/',views.user_login, name='login'),
    path('logout/',views.logout_view, name='logout'),
    path('dashboard/',views.dashboard, name='dashboard'),
    path('exam/<int:course_id>/',views.take_exam, name='take_exam')

]