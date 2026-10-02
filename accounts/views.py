import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Course , Question , Result
from .forms import CourseForm, QuestionForm

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
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
    # 1. Securely fetch ONLY the courses this student is enrolled in
    my_courses = request.user.enrolled_courses.all()
    
    # 3. Fetch past results
    past_results = Result.objects.filter(student=request.user).order_by('-date_taken')
    taken_exam_ids = past_results.values_list('exam_id', flat=True)

    context = {
        'courses': my_courses, 
        'past_results': past_results,
        'taken_exam_ids': taken_exam_ids,
    }
    
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def take_exam(request, course_id):
    course = Course.objects.get(id=course_id)

    if Result.objects.filter(student=request.user, exam=course).exists():
        messages.warning(request, 'You have already taken this exam.')
        return redirect('dashboard')

    questions = Question.objects.filter(course=course)

    if request.method == 'POST':
        score = 0
        total_questions = questions.count()
        marks_per_question = course.total_marks / total_questions if total_questions > 0 else 0
        
        # 1. Create a list to track right and wrong answers
        review_data = []

        for q in questions:
            selected_option = request.POST.get(f'question_{q.id}')
            is_correct = (selected_option == q.correct_answer)
            
            if is_correct:
                score += marks_per_question
                
            # 2. Store the data for the review page
            review_data.append({
                'question_obj': q,
                'selected_option': selected_option,
                'is_correct': is_correct
            })

        # 3. Save the result
        Result.objects.create(
            student=request.user,
            exam=course,
            marks_scored=int(score)
        )

        # 4. Render the review page instead of redirecting to the dashboard
        context = {
            'course': course,
            'score': int(score),
            'total_marks': course.total_marks,
            'review_data': review_data
        }
        return render(request, 'exam_review.html', context)

    # Normal GET request loads the exam
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

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Exam "{course.course_name}" updated successfully!')
            return redirect('teacher_dashboard')
    else:
        form = CourseForm(instance=course)
    return render(request, 'add_course.html', {'form': form, 'course': course})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Exam deleted successfully!')
        return redirect('teacher_dashboard')
        
    return render(request, 'delete_confirm.html', {'course': course})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def course_questions(request, course_id):
    # This view lists all questions for a specific exam
    course = get_object_or_404(Course, id=course_id)
    questions = Question.objects.filter(course=course)
    return render(request, 'course_questions.html', {'course': course, 'questions': questions})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            # Send them back to the list of questions
            return redirect('course_questions', course_id=question.course.id)
    else:
        form = QuestionForm(instance=question)
        
    # We can reuse the add_question form template!
    return render(request, 'add_question.html', {'form': form, 'course': question.course})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    course_id = question.course.id # Save the ID before deleting so we know where to redirect
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('course_questions', course_id=course_id)
        
    return render(request, 'delete_question.html', {'question': question})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Exam "{course.course_name}" created! Now add some questions.')
            return redirect('add_question', course_id=course.id)
    else:
        form = CourseForm()
        
    return render(request, 'add_course.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def add_question(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.course = course
            question.save()
            
            messages.success(request, 'Question added successfully!')
            return redirect('add_question', course_id=course.id)
    else:
        form = QuestionForm()
        
    context = {'form': form, 'course': course}
    return render(request, 'add_question.html', context)

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def export_results_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_results.csv"'

    writer = csv.writer(response)
    
    writer.writerow(['Student Name', 'Exam Name', 'Score'])

    results = Result.objects.all() 
    for result in results:
        writer.writerow([result.student.username, result.exam.course_name, result.marks_scored]) 

    return response


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User

def manage_students(request, course_id):
    # 1. Fetch the specific course
    course = get_object_or_404(Course, id=course_id)
    
    # 2. Security Check: Prevent other teachers from editing this roster
    if course.teacher != request.user:
        return redirect('teacher_dashboard')

    # 3. Handle the form submission when the teacher clicks "Save"
    if request.method == 'POST':
        # Get the list of selected student IDs from the HTML form checkboxes
        student_ids = request.POST.getlist('students') 
        
        # Django's .set() magic updates the ManyToMany database field instantly
        course.enrolled_students.set(student_ids)
        
        return redirect('teacher_dashboard')

    # 4. If loading the page normally, get all students to display in the list
    # (Filtering out superusers/admins so teachers only see actual students)
    all_students = User.objects.filter(is_superuser=False)
    
    context = {
        'course': course,
        'all_students': all_students,
        # We pass this so the HTML template knows which checkboxes to pre-check
        'enrolled_ids': course.enrolled_students.values_list('id', flat=True) 
    }
    
    return render(request, 'manage_students.html', context)
