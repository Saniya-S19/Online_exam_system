from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Course , Question , Result

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Account created successfully!')
        return redirect('login')
    return render(request, 'signup.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            if user.is_staff:
                return redirect('teacher_dashboard')
            else:
                return redirect('dashboard')

        else: 

            messages.error(request, "Invalid username or password.")
            return redirect('user_login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='login')
def dashboard(request):
    courses = Course.objects.all()
    past_results = Result.objects.filter(student=request.user).order_by('-date_taken')
    taken_exam_ids = past_results.values_list('exam_id', flat=True)

    context = {
        'courses': courses,
        'past_results': past_results,
        'taken_exam_ids': taken_exam_ids
        }
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def take_exam(request, course_id):
    course = Course.objects.get(id=course_id)

    if Result.objects.filter(student=request.user, exam=course).exists():
        messages.warning(request, 'You have already taken this exam.')
        return redirect('dashboard')

    questions = Question.objects.filter(course = course)

    if request.method == 'POST':
        score = 0
        total_questions = questions.count()
        marks_per_question = course.total_marks / total_questions if total_questions > 0 else 0

        for q in questions:
            selected_option = request.POST.get(f'question_{q.id}')
            if selected_option == q.correct_answer:
                score += marks_per_question

        Result.objects.create(
            student=request.user,
            exam=course,
            marks_scored=int(score)
        )

        messages.success(request, f'Exam submitted! You scored {int(score)} out of {course.total_marks}.')
        return redirect('dashboard')


    context = {
        'course': course,
        'questions': questions

    }
    return render(request, 'take_exam.html', context)

def is_teacher(user):
    return user.is_staff

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def teacher_dashboard(request):
    courses = Course.objects.all()
    all_results = Result.objects.all().order_by('-date_taken')

    total_students = User.objects.filter(is_staff=False).count()
    total_exams_taken = all_results.count()

    context = {
        'courses': courses,
        'results': all_results,
        'total_students': total_students,
        'total_exams_taken': total_exams_taken,
    }

    return render(request, 'teacher_dashboard.html', context)
