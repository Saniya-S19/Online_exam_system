import csv
import json
import random
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from .models import Course, Question, Result
from .forms import CourseForm, QuestionForm

User = get_user_model()

def is_teacher(user):
    return user.is_staff or getattr(user, 'is_teacher', False)

def home(request):
    if request.user.is_authenticated:
        if is_teacher(request.user):
            return redirect('teacher_dashboard')
        return redirect('dashboard')
    return render(request, 'home.html')

def signup(request):
    if request.user.is_authenticated:
        if is_teacher(request.user):
            return redirect('teacher_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken. Please try another one.')
            return redirect('signup')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_staff = False
            user.save()
            
            messages.success(request, 'Student account created successfully! Please log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('signup')

    return render(request, 'signup.html')

def user_login(request):
    if request.user.is_authenticated:
        if is_teacher(request.user):
            return redirect('teacher_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            if is_teacher(user):
                return redirect('teacher_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='login')
def dashboard(request):
    if is_teacher(request.user):
        return redirect('teacher_dashboard')
        
    assigned_courses = Course.objects.filter(enrolled_students=request.user)
    results = Result.objects.filter(student=request.user).order_by('-date_taken')
    
    # Map results by exam_id for quick template lookup
    results_map = {r.exam_id: r for r in results}
    completed_exam_ids = set(results_map.keys())

    # Build courses with completion status
    courses_with_status = []
    for c in assigned_courses:
        res = results_map.get(c.id)
        courses_with_status.append({
            'course': c,
            'is_completed': c.id in completed_exam_ids,
            'score': res.marks_scored if res else None,
            'result': res
        })

    # Analytics calculation
    total_assigned = assigned_courses.count()
    total_completed = results.count()
    total_score = sum(r.marks_scored for r in results)
    avg_score = round(total_score / total_completed, 1) if total_completed > 0 else 0

    context = {
        'courses': assigned_courses,
        'courses_with_status': courses_with_status,
        'results': results,
        'completed_exam_ids': list(completed_exam_ids),
        'total_assigned': total_assigned,
        'total_completed': total_completed,
        'avg_score': avg_score,
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def take_exam(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Prevent taking the exam multiple times
    existing_result = Result.objects.filter(student=request.user, exam=course).first()
    if existing_result:
        messages.warning(request, f'You have already taken "{course.course_name}". Your score is {existing_result.marks_scored}/{course.total_marks}.')
        return redirect('dashboard')

    questions = Question.objects.filter(course=course)

    if request.method == 'POST':
        score = 0
        total_questions = questions.count()
        marks_per_question = course.total_marks / total_questions if total_questions > 0 else 0
        review_data = []

        for q in questions:
            selected_option = request.POST.get(f'question_{q.id}')
            is_correct = (selected_option == q.correct_answer)
            
            if is_correct:
                score += marks_per_question
                
            review_data.append({
                'question_obj': q,
                'selected_option': selected_option,
                'is_correct': is_correct
            })

        final_score = int(round(score))
        Result.objects.create(
            student=request.user,
            exam=course,
            marks_scored=final_score
        )

        context = {
            'course': course,
            'score': final_score,
            'total_marks': course.total_marks,
            'review_data': review_data,
            'total_questions': total_questions,
            'correct_count': sum(1 for item in review_data if item['is_correct']),
        }
        return render(request, 'exam_review.html', context)

    context = {
        'course': course,
        'questions': questions
    }
    return render(request, 'take_exam.html', context)

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def teacher_dashboard(request):
    courses = Course.objects.all()
    all_results = Result.objects.all().order_by('-date_taken')

    total_students = User.objects.filter(is_staff=False).count()
    total_exams_created = courses.count()
    total_exams_taken = all_results.count()

    context = {
        'courses': courses,
        'results': all_results,
        'total_students': total_students,
        'total_exams_created': total_exams_created,
        'total_exams_taken': total_exams_taken,
    }
    return render(request, 'teacher_dashboard.html', context)

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            form.save_m2m()
            messages.success(request, f'Exam "{course.course_name}" created! Add questions now.')
            return redirect('add_question', course_id=course.id)
    else:
        form = CourseForm()
        
    return render(request, 'add_course.html', {'form': form})

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
        course_name = course.course_name
        course.delete()
        messages.success(request, f'Exam "{course_name}" deleted successfully!')
        return redirect('teacher_dashboard')
    return render(request, 'delete_confirm.html', {'course': course})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def course_questions(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = Question.objects.filter(course=course)
    return render(request, 'course_questions.html', {'course': course, 'questions': questions})

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
            return redirect('course_questions', course_id=course.id)
    else:
        form = QuestionForm()
        
    context = {'form': form, 'course': course}
    return render(request, 'add_question.html', context)

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('course_questions', course_id=question.course.id)
    else:
        form = QuestionForm(instance=question)
        
    return render(request, 'add_question.html', {'form': form, 'course': question.course, 'question': question})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    course_id = question.course.id
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('course_questions', course_id=course_id)
        
    return render(request, 'delete_question.html', {'question': question})

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def manage_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    students = User.objects.filter(is_staff=False, is_superuser=False).order_by('username')
    
    if request.method == 'POST':
        selected_student_ids = request.POST.getlist('students')
        course.enrolled_students.set(selected_student_ids)
        messages.success(request, f'Student enrollment updated for "{course.course_name}"!')
        return redirect('teacher_dashboard')
        
    return render(request, 'manage_students.html', {
        'course': course,
        'students': students,
        'enrolled_ids': list(course.enrolled_students.values_list('id', flat=True))
    })

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def export_results_csv(request, course_id=None):
    response = HttpResponse(content_type='text/csv')
    filename = "student_results.csv" if not course_id else f"results_exam_{course_id}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Student Username', 'Exam Name', 'Score', 'Date Taken'])

    if course_id:
        results = Result.objects.filter(exam_id=course_id).order_by('-date_taken')
    else:
        results = Result.objects.all().order_by('-date_taken')

    for result in results:
        date_str = result.date_taken.strftime("%Y-%m-%d %H:%M") if hasattr(result, 'date_taken') and result.date_taken else ''
        writer.writerow([result.student.username, result.exam.course_name, result.marks_scored, date_str])

    return response

# =========================================================================
# SMART AI ENHANCEMENTS (No database changes required)
# =========================================================================

AI_QUESTION_BANK = {
    'python': [
        {
            'question_text': 'What is the output of print(type([]) is list)?',
            'option1': 'True',
            'option2': 'False',
            'option3': 'TypeError',
            'option4': 'None',
            'correct_answer': 'True',
        },
        {
            'question_text': 'Which of the following data structures in Python is immutable?',
            'option1': 'Tuple',
            'option2': 'List',
            'option3': 'Dictionary',
            'option4': 'Set',
            'correct_answer': 'Tuple',
        },
        {
            'question_text': 'Which keyword is used to create an anonymous function in Python?',
            'option1': 'lambda',
            'option2': 'def',
            'option3': 'anon',
            'option4': 'inline',
            'correct_answer': 'lambda',
        },
        {
            'question_text': 'What does the __init__ method do in a Python class?',
            'option1': 'Initializes object attributes upon instantiation',
            'option2': 'Destroys the object when memory is full',
            'option3': 'Imports external libraries automatically',
            'option4': 'Compiles the class to bytecode',
            'correct_answer': 'Initializes object attributes upon instantiation',
        },
        {
            'question_text': 'How do you handle exceptions in Python?',
            'option1': 'try...except block',
            'option2': 'catch...throw block',
            'option3': 'do...rescue block',
            'option4': 'check...error block',
            'correct_answer': 'try...except block',
        }
    ],
    'javascript': [
        {
            'question_text': 'What does "typeof NaN" return in JavaScript?',
            'option1': 'number',
            'option2': 'NaN',
            'option3': 'undefined',
            'option4': 'object',
            'correct_answer': 'number',
        },
        {
            'question_text': 'Which method is used to parse a JSON string into a JavaScript object?',
            'option1': 'JSON.parse()',
            'option2': 'JSON.stringify()',
            'option3': 'JSON.objectify()',
            'option4': 'JSON.toObject()',
            'correct_answer': 'JSON.parse()',
        },
        {
            'question_text': 'What is the purpose of the "use strict" directive in JavaScript?',
            'option1': 'Enforces stricter parsing and error handling at runtime',
            'option2': 'Forces code to compile into TypeScript',
            'option3': 'Disables all asynchronous functions',
            'option4': 'Optimizes graphics rendering in canvas',
            'correct_answer': 'Enforces stricter parsing and error handling at runtime',
        }
    ],
    'sql': [
        {
            'question_text': 'Which SQL clause is used to filter records based on aggregate functions?',
            'option1': 'HAVING',
            'option2': 'WHERE',
            'option3': 'GROUP BY',
            'option4': 'ORDER BY',
            'correct_answer': 'HAVING',
        },
        {
            'question_text': 'What does a FULL OUTER JOIN return?',
            'option1': 'All rows when there is a match in one of the tables',
            'option2': 'Only rows that match in both tables',
            'option3': 'Only rows from the left table',
            'option4': 'The Cartesian product of both tables',
            'correct_answer': 'All rows when there is a match in one of the tables',
        }
    ],
    'dsa': [
        {
            'question_text': 'What is the worst-case time complexity of QuickSort?',
            'option1': 'O(n^2)',
            'option2': 'O(n log n)',
            'option3': 'O(n)',
            'option4': 'O(log n)',
            'correct_answer': 'O(n^2)',
        },
        {
            'question_text': 'Which data structure follows the Last-In-First-Out (LIFO) principle?',
            'option1': 'Stack',
            'option2': 'Queue',
            'option3': 'Binary Search Tree',
            'option4': 'Linked List',
            'correct_answer': 'Stack',
        }
    ],
    'general': [
        {
            'question_text': 'What is the primary function of an Operating System kernel?',
            'option1': 'Bridge between hardware and software applications',
            'option2': 'Design user interface animations',
            'option3': 'Format hard drives upon boot',
            'option4': 'Host website domains',
            'correct_answer': 'Bridge between hardware and software applications',
        },
        {
            'question_text': 'In computer networking, what does DNS stand for?',
            'option1': 'Domain Name System',
            'option2': 'Dynamic Network Storage',
            'option3': 'Data Node Server',
            'option4': 'Distributed Network Socket',
            'correct_answer': 'Domain Name System',
        }
    ]
}

@login_required(login_url='login')
@user_passes_test(is_teacher, login_url='dashboard')
def generate_ai_question_api(request):
    """
    Smart AI Question Generator endpoint for instructors.
    Generates tailored multiple-choice questions for exams instantly.
    """
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            category = body.get('category', 'python').lower()
            topic = body.get('topic', '').strip().lower()

            # Attempt category match
            pool = None
            if topic:
                for key in AI_QUESTION_BANK:
                    if key in topic:
                        pool = AI_QUESTION_BANK[key]
                        break

            if not pool:
                pool = AI_QUESTION_BANK.get(category, AI_QUESTION_BANK['python'])

            question = random.choice(pool)
            return JsonResponse({'status': 'success', 'question': question})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
